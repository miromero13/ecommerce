"""Intérprete local (reglas, sin IA ni red) de frases en español -> AnalyticsQuery.

Pensado para texto escrito y dictado (sin tildes, sin puntuación, números en palabras). Funciona por RANURAS:
1. normaliza y tokeniza; los nombres del catálogo se reemplazan por marcas (_b, _p, _c);
2. cada ranura (tipo de reporte, comparación, período, pago, canal, métrica, ranking, agrupación) busca sus
   patrones (report_language/lexicon.py) y CONSUME las palabras que usa;
3. regla de oro: si sobra una palabra de una familia conocida (un mes, "hace", "ganancia", un número...) que
   ninguna ranura pudo usar, devuelve None en vez de responder otra pregunta; el relleno se ignora;
4. resuelve las ranuras según las convenciones de docs/superpowers/plans/2026-11-11-reportes-lenguaje-natural.md.
Antes de todo se expanden abreviaturas ("vtas", "suc", "x"); si sobran palabras desconocidas se intenta UNA segunda
pasada corrigiendo tipeos (report_language/fuzzy.py). Las palabras de contenido que siguen sin usarse ("ventas de
zapatos") se devuelven como avisos (interpret_locally_detailed).
"""
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date, timedelta
from uuid import UUID

from app.schemas.analytics_schema import TIME_DIMENSIONS, AnalyticsQuery, PeriodSpec
from app.services.report_language import lexicon as L
from app.services.report_language.fuzzy import corrector_for
from app.services.report_language.periods import PERIOD_RULES, InvalidPeriod, bounds, to_int

SALES_KIND, STOCK_KINDS = "sales", ("inventory", "critical_stock")
UNITS_DIMS = {"product", "variant", "size", "color", "category"}  # ranking por estas -> unidades; resto -> ingresos
MAX_WARNINGS = 5
MAX_CLAUSES = 12
CONTENT_PREPS = {"de", "del", "para", "en", "con", "sobre", "desde"}  # "ventas de zapatos": lo que sigue es contenido
NAME_ARTICLES = {"el", "la", "los", "las", "un", "una", "unos", "unas", "su", "sus", "mi", "mis", "nuestra", "nuestro"}


@dataclass
class Catalog:
    """Nombres NORMALIZADOS (ver normalize) -> id."""
    branches: dict[str, UUID] = field(default_factory=dict)
    products: dict[str, UUID] = field(default_factory=dict)
    categories: dict[str, UUID] = field(default_factory=dict)


def normalize(text: str) -> str:
    """Minúsculas, sin tildes, sin puntuación (salvo '/' y dígitos), espacios colapsados."""
    text = unicodedata.normalize("NFKD", text.lower())  # NFKD: también pliega ancho completo ("ｖｅｎｔａｓ")
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return " ".join(re.sub(r"[^a-z0-9/\s]", " ", text).split())


class _Sentence:
    """Tokens de la frase; los consumidos por una ranura se reemplazan por una marca que empieza con '_'."""

    def __init__(self, tokens: list[str]):
        self.toks = tokens

    @property
    def text(self) -> str:
        return " ".join(self.toks)

    def take(self, pattern: re.Pattern, marker: str = "_"):
        """Busca, consume y devuelve (match, índice del primer token) hasta que el patrón no coincida más."""
        while True:
            text = self.text
            m = pattern.search(text)
            if not m or m.end() == m.start():
                return
            start, end = text.count(" ", 0, m.start()), text.count(" ", 0, m.end() - 1)
            self.toks[start:end + 1] = [marker] * (end - start + 1)
            yield m, start

    def take_at(self, pattern: re.Pattern, index: int):
        """Como take, pero solo si el patrón coincide justo desde el token `index`."""
        if index >= len(self.toks):
            return None
        text = self.text
        pos = len(" ".join(self.toks[:index])) + (1 if index else 0)
        m = pattern.match(text, pos - 1 if index else 0)  # el patrón empieza con el espacio separador
        if not m or m.end() == m.start():
            return None
        start, end = text.count(" ", 0, m.start() + 1), text.count(" ", 0, m.end() - 1)
        self.toks[start:end + 1] = ["_"] * (end - start + 1)
        return m


def _numbers_to_digits(toks: list[str]) -> list[str]:
    """'treinta y cinco' -> '35', 'dos mil veinticinco' -> '2025', 'diez' -> '10'."""
    out, i = [], 0
    while i < len(toks):
        w = toks[i]
        if w not in L.NUM_WORDS or (w in ("un", "una", "uno") and not (
                toks[i + 1:i + 2] and toks[i + 1] in L.UNIT_AFTER_ONE or out[-1:] == ["top"]
                or w == "uno" and toks[i + 1:i + 2] == ["de"] and toks[i + 2:i + 3] and toks[i + 2] in L.MONTHS)):
            out.append(w)
            i += 1
            continue
        total, current = 0, 0
        while i < len(toks):
            w = toks[i]
            if w == "y" and i + 1 < len(toks) and toks[i - 1] in L.NUM_TENS and toks[i + 1] in L.NUM_UNITS:
                i += 1
                continue
            if w not in L.NUM_WORDS:
                break
            if w == "mil":
                total += max(current, 1) * 1000
                current = 0
            else:
                current += L.NUM_WORDS[w]
            i += 1
        out.append(str(total + current))
    return out


def _match_catalog(s: _Sentence, catalog: Catalog) -> dict[str, list[UUID]]:
    """Nombres completos (el más largo primero, sin reutilizar palabras) y luego palabras distintivas
    ('sur' -> Ayni Zona Sur) cuando aparecen en un solo nombre de todo el catálogo. Se compara en singular
    ('faldas plisadas' = 'Falda Plisada', 'blusa' = 'Blusas')."""
    lists = (("branch", "_b", catalog.branches), ("product", "_p", catalog.products),
             ("category", "_c", catalog.categories))
    found: dict[str, list[UUID]] = {"branch": [], "product": [], "category": []}
    names = sorted(((n, kind, marker, id_) for kind, marker, d in lists for n, id_ in d.items() if n),
                   key=lambda x: -len(x[0]))
    toks = s.toks
    singular = [_singular(t) for t in toks]
    present = set(singular)
    for name, kind, marker, id_ in names:
        words = [_singular(w) for w in name.split()]
        if not set(words) <= present:  # filtro barato
            continue
        for i in range(len(toks) - len(words) + 1):
            if singular[i:i + len(words)] == words and not any(t.startswith("_") for t in toks[i:i + len(words)]):
                toks[i:i + len(words)] = [marker] * len(words)
                if id_ not in found[kind]:
                    found[kind].append(id_)
    # Palabra distintiva suelta: SOLO sucursales ("sur", "el alto", "en el centro"); productos y categorías necesitan
    # el nombre completo ("básica" no es "Polera Básica", "cuero" no es "Chaqueta de Cuero").
    owners: dict[str, set] = {}
    next_word: dict[tuple, str] = {}  # (sucursal, palabra) -> palabra siguiente del nombre ("zona" -> "sur")
    for name, kind, marker, id_ in names:
        words = [_singular(w) for w in name.split()]
        for k, word in enumerate(words):
            owners.setdefault(word, set()).add((kind, marker, id_))
            if k + 1 < len(words) and _classify(words[k + 1]) == "unknown":
                next_word[(id_, word)] = words[k + 1]
    for i, tok in enumerate(toks):
        owner = owners.get(_singular(tok))
        if not owner or len(owner) != 1 or len(tok) < 3 or _classify(tok) != "unknown":
            continue
        kind, marker, id_ = next(iter(owner))
        if kind != "branch":
            continue
        prev = toks[i - 1] if i else ""
        after = toks[i + 1] if i + 1 < len(toks) else ""
        if prev in L.INTENSIFIERS or prev == "lo":
            continue  # "el más alto", "a lo largo", "lo alto" no son la sucursal El Alto
        follow = next_word.get((id_, _singular(tok)))
        if follow and _singular(after) != follow:
            continue  # "zona" sola o "zona norte" no es "Zona Sur": falta la palabra que sigue en el nombre
        if not follow and _classify(after) == "unknown" and owners.get(_singular(after)) != owner \
                and not L.SALES_NEAR.fullmatch(after):
            continue  # "centro comercial": la palabra siguiente cambia el sentido
        if _names_another_branch(toks, i, owners, id_):
            continue  # "el centro de cochabamba" es Cochabamba, no la suma de dos sucursales
        near = [toks[j] for j in (i - 1, i + 1) if 0 <= j < len(toks)]
        after_article = prev in L.PLACE_ARTICLES  # "en el centro", "la zona sur", "del alto"
        if not after_article and any(_classify(w) in ("unknown", "number") and owners.get(_singular(w)) != owner
                                     and not L.SALES_NEAR.fullmatch(w) for w in near):
            continue  # pegada a otra palabra desconocida: es parte de otro nombre ("Product 1 active")
        s.toks[i] = marker
        if id_ not in found[kind]:
            found[kind].append(id_)
    return found


def _unknown_branch_named(toks: list[str]) -> bool:
    """'la tienda de Santa Cruz', 'el local de Sopocachi', 'la sede de Potosí': nombre de sucursal que no existe."""
    for i, tok in enumerate(toks[:-2]):
        if L.BRANCH_NOUNS.fullmatch(tok) and toks[i + 1] in ("de", "del"):
            j = i + 2
            while j < len(toks) and toks[j] in ("el", "la", "los", "las"):
                j += 1
            if j < len(toks) and _classify(toks[j]) == "unknown":
                return True
    return False


def _person_as_filter(words: list[str]) -> bool:
    """'ventas del vendedor juan', 'lo que vendió la cajera': una persona usada como filtro (no existe). Que una
    persona pida el reporte ('el contador quiere…') no cambia nada."""
    for i, w in enumerate(words):
        if not L.ROLE.fullmatch(w):
            continue
        j = i - 1
        while j >= 0 and words[j] in L.PERSON_DETERMINERS:
            j -= 1
        if j >= 0 and (words[j] in ("de", "del") or re.fullmatch(L.VEND, words[j]) or L.MOVED_RE.fullmatch(words[j])):
            return True
    return False


def _names_another_branch(toks: list[str], i: int, owners: dict, id_) -> bool:
    """'centro de cochabamba', 'centro de el alto': tras 'de' viene otra sucursal (marca o palabra distintiva)."""
    j = i + 1
    if j >= len(toks) or toks[j] not in ("de", "del"):
        return False
    while j < len(toks) and toks[j] in ("de", "del", "el", "la"):
        j += 1
    if j >= len(toks):
        return False
    if _classify(toks[j]) == "unknown" and toks[j] not in owners:
        return True  # "el centro de Santa Cruz": es el centro de otro lugar
    other = owners.get(_singular(toks[j]), set())
    return toks[j] == "_b" or (len(other) == 1 and next(iter(other))[0] == "branch" and next(iter(other))[2] != id_)


def _names_unknown(toks: list[str], i: int) -> bool:
    """'la sucursal (de) Norte', 'la categoría Zapatos', 'el producto X': el sustantivo de tipo va seguido de un nombre
    que no está en el catálogo -> se pidió algo que no existe (aclaración 24). 'cuál sucursal factura más' es una
    pregunta: lo que sigue es un verbo."""
    if i and toks[i - 1] in ("que", "cual", "cuales"):
        return False
    j = i + 1
    while j < len(toks) and toks[j] in ("de", "del", "la", "el", "los", "las"):
        j += 1
    return j < len(toks) and _classify(toks[j]) == "unknown" and not L.SALES_NEAR.fullmatch(toks[j])


def _lists_dimension(toks: list[str], i: int) -> bool:
    """'listado de sucursales', 'tabla de productos': hay una dimensión en plural a 1-3 palabras."""
    return toks[i + 1:i + 2] == ["de"] and any(re.fullmatch(L.DIM_PLURAL, t) for t in toks[i + 2:i + 5])


def _singular(word: str) -> str:
    """Singular aproximado para comparar nombres: 'colores' -> 'color', 'faldas' -> 'falda', 'jeans' -> 'jean'."""
    if len(word) > 4 and word.endswith("es") and word[-3] in "lrndzj":
        return word[:-2]
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def _classify(tok: str) -> str:
    if tok.startswith("_"):
        return "used"
    if L.ROLE.fullmatch(tok):
        return "role"
    if tok in L.STOP or not re.search(r"[a-z0-9]", tok):
        return "stop"
    if re.fullmatch(r"[\d/]+", tok):
        return "number"
    if L.FLAG.fullmatch(tok):
        return "flag"
    return "unknown"


def _dim(word: str) -> str:
    return next(d for d, p in L.DIM_WORDS.items() if re.fullmatch(p, word))


def _is_plural(word: str) -> bool:
    return word.split()[0].endswith("s") and word != "mes"


def _ranking(s: _Sentence):
    """'mas/menos' cerca de una palabra de ventas, 'mejor/peor', 'top', 'ranking'.
    Devuelve (orden o None, pista de singular, métrica sugerida por 'más usado', si habla de lo 'vendido')."""
    orders, singular, used_metric, sold = set(), False, None, False
    toks = s.toks
    for i, tok in enumerate(toks):
        if tok in ("mas", "menos"):
            near = []
            for step in (-1, 1):
                j = i + step
                while 0 <= j < len(toks) and toks[j] in L.RANK_SKIP:
                    j += step
                if 0 <= j < len(toks):
                    near.append(toks[j])
            if not any(L.SALES_NEAR.fullmatch(w) for w in near):
                continue
            # "lo más vendido", "las más vendidas", "lo que más se vende": producto implícito (ancla por sí solo);
            # "el que más vende" no (¿quién?)
            sold = sold or any(L.SOLD.fullmatch(w) for w in near) or "se" in toks[max(0, i - 2):i + 2] \
                or toks[max(0, i - 2):i] == ["lo", "que"]
            if any(L.USED.fullmatch(w) for w in near):
                used_metric = "orders"
            low = any(L.LOW.fullmatch(w) for w in near)
            orders.add("desc" if (tok == "mas") != low else "asc")
            for j in (i - 2, i - 1, i + 1, i + 2):  # "más bajas", "usan más": el modificador es parte del ranking
                if 0 <= j < len(toks) and (L.LOW.fullmatch(toks[j]) or L.USED.fullmatch(toks[j])
                                           or re.fullmatch(r"alt[oa]s?|elevad[oa]s?", toks[j])):
                    toks[j] = "_"
        elif tok in L.RANK_LIST or tok in ("listado", "tabla") and _lists_dimension(toks, i):
            # "el top de productos", "rankin de sucursales", "listado de sucursales": ranking, no singular
            orders.add("desc")
            _no_role_near(toks, i)
            toks[i] = "_"
            continue
        elif tok in L.RANK_DESC:
            orders.add("desc")
        elif tok in L.RANK_ASC:
            orders.add("asc")
        else:
            continue
        _no_role_near(toks, i)
        if i and toks[i - 1] in ("el", "la"):
            singular = True
        toks[i] = "_"
    if len(orders) > 1:
        raise _Ambiguous("ranking con 'más' y 'menos' a la vez")
    return (orders.pop() if orders else None), singular, used_metric, sold


def _anchored(words, kind, metric, status, ranking, sales_verb, candidates, found, cue_groups, compared,
              period, implied_product, channel=False) -> bool:
    """Regla de oro, parte 2: un pedido necesita un ANCLA. Sin ella ("mejor", "pero ahora por sucursal", "otra vez
    pero peor", "ayer") la frase se refiere a algo que el intérprete no ve -> None.
    Anclas: tipo de reporte; métrica o palabra de dinero/ventas; pregunta de estado; comparación que nombra lo
    comparado. Un ranking además se ancla con un sustantivo de entidad, un nombre del catálogo, una agrupación o una
    pregunta ("¿qué se vendió más?"); fuera de un ranking, un verbo de venta ancla ("cuánto vendimos") y una agrupación
    solo ancla con un sustantivo de entidad ("productos por categoría") o un período dicho ("x medio de pago de hoy");
    "pero ahora por sucursal" o "por día" a secas no."""
    # "lo de la tienda", "lo de internet": lo vendido en ese canal
    said_what = channel and re.search(r"(?:^| )lo (?:de|del|que) ", " ".join(words))
    base = (kind != SALES_KIND or metric or status or compared or said_what
            or any(L.SALES_NOUN.fullmatch(w) or L.MONEY_VERB.fullmatch(w) for w in words))
    entity = bool(candidates) or any(found.values())
    if ranking:
        # "la venta más alta", "el ticket más alto": rankean ventas sueltas (no hay ese reporte) -> sin ancla
        return bool(compared or entity or cue_groups or implied_product or _asks_question(words))
    return bool(base or sales_verb or cue_groups and (entity or period is not None))


def _asks_question(words: list[str]) -> bool:
    """'¿qué se vendió más?', 'en qué día…', 'dime cuál…' (no el relativo de 'el que más vende')."""
    return any(w in L.QUESTION_WORDS and (i == 0 or words[i - 1] in L.BEFORE_QUESTION) for i, w in enumerate(words))


def _no_role_near(toks: list[str], i: int) -> None:
    """'el mejor vendedor', 'ranking de cajeros': no existe rankear personas del personal."""
    if any(L.ROLE.fullmatch(t) for t in toks[max(0, i - 3):i + 4]):
        raise _Ambiguous("ranking de personas (vendedor, cajero...): no hay esa dimensión")


class _Ambiguous(Exception):
    """La frase tiene algo reconocido que no sabemos resolver: no se responde (regla de oro)."""


def interpret_locally(text: str, catalog: Catalog, today: date | None = None) -> AnalyticsQuery | None:
    """Frase -> AnalyticsQuery, o None si no se entiende o tiene una parte reconocida que no se sabe resolver."""
    return interpret_locally_detailed(text, catalog, today)[0]


def interpret_locally_detailed(text: str, catalog: Catalog,
                               today: date | None = None) -> tuple[AnalyticsQuery | None, list[str]]:
    """Como interpret_locally, más las palabras de contenido toleradas pero no aplicadas (máx. 5, sin repetir).

    Frases largas ("soy doña Rosa, no sé de computadoras, pero dígame cuánto vendimos ayer") se parten en cláusulas;
    las que no tienen ninguna ranura reconocida son conversación y se descartan (ni regla de oro ni avisos)."""
    today = today or date.today()
    clauses = _clauses(text)
    if len(clauses) > MAX_CLAUSES:
        return None, []  # no se trunca en silencio: el pedido podría estar en la parte cortada
    every = [t for _, c in clauses for t in c]
    if len(clauses) == 1:
        return _detailed(every, catalog, today)
    # 1) sin las cláusulas de pura conversación ni las explicaciones ("porque…")
    kept = _select_clauses(clauses, catalog, today)
    if kept and len(kept) < len(clauses):
        spec, words = _detailed([t for c in kept for t in c], catalog, today)
        if spec is not None:
            return spec, words
    # 2) la frase entera
    spec, words = _detailed(every, catalog, today)
    if spec is not None:
        return spec, words
    # 3) si todo junto no se puede resolver, un pedido completo introducido por "pero (ahora)", "dígame",
    #    "quiero saber"... reemplaza el contexto anterior ("el año pasado vendíamos más, pero ahora quiero ver…")
    for k in range(len(clauses) - 1, 0, -1):
        dropped = [t for _, c in clauses[:k] for t in c]
        if clauses[k][0] in L.PIVOT_CONNECTORS and not _names_a_filter(dropped, catalog):
            rest = clauses[k:]
            kept = _select_clauses(rest, catalog, today) or [c for _, c in rest]
            spec, words = _detailed([t for c in kept for t in c], catalog, today)
            if spec is not None:
                return spec, words
    return None, []


def _names_a_filter(tokens: list[str], catalog: Catalog) -> bool:
    """¿Lo que se descartaría nombra una sucursal/producto/categoría o una exclusión? Entonces no se descarta."""
    s = _Sentence(list(tokens))
    found = _match_catalog(s, catalog)
    return any(found.values()) or any(L.FILTER_WORDS.fullmatch(t) for t in s.toks)


def _select_clauses(clauses: list[tuple[str, list[str]]], catalog: Catalog, today: date) -> list[list[str]]:
    """Lo que sigue a "porque / aunque / ya que" es una explicación y se descarta si hay otra cláusula con ranuras;
    se descartan las cláusulas sin ninguna ranura (conversación)."""
    scored = [(connector, c, _slot_score(c, catalog, today)) for connector, c in clauses]
    if any(score and connector not in L.ASIDE_CONNECTORS for connector, _, score in scored):
        scored = [x for x in scored if x[0] not in L.ASIDE_CONNECTORS]
    return [c for _, c, score in scored if score > 0]


def _expand(tokens: list[str]) -> list[str]:
    """Abreviaturas de teléfono; las que tienen plural lo toman tras un número o un determinante plural
    ("los 3 prod más vendidos" -> productos)."""
    out: list[str] = []
    for tok in tokens:
        if tok in L.ABBREVIATIONS_NUMBER:
            singular, plural = L.ABBREVIATIONS_NUMBER[tok]
            prev = out[-1] if out else ""
            out.append(plural if prev in L.PLURAL_DETERMINERS or (prev.isdigit() and prev != "1") else singular)
        else:
            out.extend(L.ABBREVIATIONS.get(tok, tok).split())
    return out


def _clauses(text: str) -> list[tuple[str, list[str]]]:
    """Cláusulas (conector que la introduce, tokens): se corta en puntuación, en conectores ("pero", "porque",
    "ya que"...) y antes de lo que introduce el pedido ("dígame", "quiero saber"...). Un trozo sin conector que
    empieza con preposición o "y" ("de ayer", "y por sucursal") continúa la cláusula anterior."""
    clauses: list[tuple[str, list[str]]] = []
    for chunk in re.split(r"[,.;:!?¿¡\n]+", text):
        parts = L.CLAUSE_SPLIT.split(" " + " ".join(_expand(normalize(chunk).split())) + " ")
        connector = ""
        for i, part in enumerate(parts):
            if i % 2:  # separador capturado (None cuando se cortó antes de "dígame / quiero saber")
                connector = part or "ask"  # None: se cortó antes de "dígame / quiero saber"
                continue
            toks = part.split()
            if not toks:
                continue
            if clauses and not connector and toks[0] in CONTENT_PREPS | {"y", "e", "o", "por"}:
                clauses[-1][1].extend(toks)
            else:
                clauses.append((connector, toks))
            connector = ""
    return clauses or [("", [])]


def _slot_score(tokens: list[str], catalog: Catalog, today: date) -> int:
    """Cuántas palabras de la cláusula usó alguna ranura (sin contar relleno ni un sustantivo singular suelto)."""
    _, s = _run(tokens, catalog, today)
    return sum(1 for t in s.toks if t.startswith("_") and t not in ("_f", "_n"))


def _detailed(tokens: list[str], catalog: Catalog, today: date) -> tuple[AnalyticsQuery | None, list[str]]:
    spec, s = _run(tokens, catalog, today)
    unknown = [t for t in s.toks if _classify(t) == "unknown"]
    if unknown:  # segunda pasada: corrige tipeos SOLO en lo que no se pudo usar
        names = frozenset(w for d in (catalog.branches, catalog.products, catalog.categories)
                          for name in d for w in name.split() if len(w) >= 5 and w.isalpha())
        corrector = corrector_for(names)
        fixes = {t: fixed for t in dict.fromkeys(unknown[:20]) if (fixed := corrector.correct(t))}
        if fixes:
            spec2, s2 = _run([fixes.get(t, t) for t in tokens], catalog, today)
            if spec2 is not None or spec is None:
                spec, s = spec2, s2
    return spec, (_content_words(s.toks) if spec is not None else [])


def _run(tokens: list[str], catalog: Catalog, today: date) -> tuple[AnalyticsQuery | None, "_Sentence"]:
    s = _Sentence(list(tokens))
    try:
        return _interpret(s, catalog, today), s
    except (_Ambiguous, InvalidPeriod, ValueError, OverflowError):
        return None, s


def _content_words(toks: list[str]) -> list[str]:
    """Palabras desconocidas que parecen contenido: siguen a 'de/en/para...' (salteando artículos), siguen justo a
    una ranura usada ('cuánto vendió Miraflores', 'ventas zapatos') o continúan un nombre ya avisado o del catálogo
    ('de zapatos y carteras', 'de santa cruz'). El relleno nunca aparece."""
    warned: list[str] = []
    for i, tok in enumerate(toks):
        if _classify(tok) != "unknown":
            continue
        j = i - 1
        while j >= 0 and toks[j] in NAME_ARTICLES:
            j -= 1
        prev = toks[j] if j >= 0 else ""
        before = toks[j - 1] if j >= 1 else ""
        after_slot = prev.startswith("_") and prev != "_f" and tok not in L.HARMLESS_AFTER_SLOT
        if prev in CONTENT_PREPS or after_slot or (_classify(prev) in ("unknown", "number") and prev in warned or
                                     prev.isdigit() and before in warned) or \
                (prev in ("y", "e", "o", "u") and (before in warned or before in ("_b", "_p", "_c"))):
            if tok not in warned:
                warned.append(tok)
    return warned[:MAX_WARNINGS]


def _interpret(s: "_Sentence", catalog: Catalog, today: date) -> AnalyticsQuery | None:
    asks_one = "cual" in s.toks and "cuales" not in s.toks  # "de todas las sucursales, ¿cuál vendió más?"
    pair_cue = bool(re.search(r"(?:^| )(?:(?:mas|menos|mejor|peor) que|vs|versus|contra|compar\w*)(?: |$)",
                              " ".join(s.toks)))  # "la sur vende más que la del alto"
    words = list(s.toks)  # la frase original, para el ancla
    found = _match_catalog(s, catalog)
    s.toks = _numbers_to_digits(s.toks)
    list(s.take(L.FILLER, "_f"))  # relleno: no cuenta como ranura

    # "las ventas y el ticket promedio", "cuanto vendimos y cuantos pedidos hubo": dos reportes a la vez
    for m in L.METRIC_PAIR.finditer(" ".join(s.toks)):
        metrics = {k for word in (m.group("first"), m.group("second"))
                   for k, pattern in L.METRIC_WORDS.items() if re.fullmatch(pattern, word)}
        if len(metrics) > 1:
            return None

    # pagos que no existen, mayoreo, días de la semana habituales: no hay ese reporte
    if L.UNSUPPORTED.search(" ".join(s.toks)) or _person_as_filter(words) or _unknown_branch_named(s.toks):
        return None

    # tipo de reporte
    kinds = {kind for kind, pattern in L.KINDS for _ in s.take(pattern)}
    if len(kinds) > 1:
        return None
    kind = kinds.pop() if kinds else SALES_KIND
    if kind != SALES_KIND and any(L.MONEY_VERB.fullmatch(w) for w in words):
        return None  # "cuánto cobramos de inventario": dinero y stock no se mezclan

    # agrupaciones que parecen comparaciones ("comparame las sucursales", "online vs tienda")
    groups: list[tuple[int, str]] = [(i, _dim(m.group("d") or m.group("e"))) for m, i in s.take(L.GROUP_COMPARE)]
    compared_entities = bool(groups)  # "comparame las sucursales": nombra lo que se compara
    channel_group = bool(list(s.take(L.CHANNEL_VS)))
    payment_group = bool(list(s.take(L.PAYMENT_VS)))
    if payment_group:
        groups.append((-1, "payment_method"))

    # comparación con el período anterior y períodos
    markers, explicit_target = [], False  # explicit_target: "comparado con el anterior" ya nombró el período previo
    for m, i in s.take(L.COMPARE):
        markers.append((i, i + len(m.group(0).split()), bool(re.search(r"(?:^| )(?:con|a|al|vs|versus|contra)$",
                                                                     m.group(0)))))
        explicit_target = explicit_target or bool(re.search(r"(?:anterior|previo|pasad[oa])$", m.group(0)))
    if markers:
        explicit_target = bool(list(s.take(L.COMPARE_TARGET))) or explicit_target
    periods = [(i, rule(m, today)) for pattern, rule in PERIOD_RULES for m, i in s.take(pattern)]
    periods.sort(key=lambda p: p[0])
    if markers and len(periods) == 2:
        # "este mes comparado con el mes pasado", "compara octubre con septiembre": el primero es el pedido y el
        # segundo la referencia, que debe ser el período inmediatamente anterior (el motor compara con ese)
        (_, main), (_, base) = periods
        main_from, _ = bounds(main, today)
        base_from, base_to = bounds(base, today)
        if base_to + timedelta(days=1) != main_from or base_from > base_to:
            return None  # la referencia debe terminar justo el día antes ("hoy vs el lunes", "octubre vs agosto": no)
        periods, explicit_target = periods[:1], True
    elif markers and len(periods) == 1 and not any(len(ids) >= 2 for ids in found.values()) and             any(connector and periods[0][0] >= end for _, end, connector in markers):
        return None  # "ventas comparado con ayer": falta el período pedido
    if len(periods) > 1:
        return None
    period = periods[0][1] if periods else None

    # ranking: top N y dirección (antes de las métricas: "con más pedidos" necesita ver "pedidos")
    top_n = None
    for m, _ in s.take(L.TOP_N):
        top_n = max(1, min(to_int(next(g for g in m.group("a", "b", "c", "d", "e") if g)), 50))
    order, singular, used_metric, sold = _ranking(s)
    ranking = order is not None or top_n is not None

    # agrupaciones explícitas ("por X", "de cada X", "diario") y su cadena ("por sucursal y canal")
    for m, i in s.take(L.GROUP_CUE):
        groups.append((i, _dim(m.group("d"))))
        nxt = i + 1
        while nxt < len(s.toks) and s.toks[nxt] == "_":
            nxt += 1
        while (chained := s.take_at(L.GROUP_CHAIN, nxt)) is not None:
            groups.append((nxt, _dim(chained.group("d"))))
            while nxt < len(s.toks) and s.toks[nxt] == "_":
                nxt += 1
    for pattern, dim in L.DIM_TIME_ADJ:
        groups.extend((i, dim) for _, i in s.take(pattern))
    for pattern, _ in L.HEAD_NOUNS:
        list(s.take(pattern))

    # filtros de pago y canal
    payments = [method for method, pattern in L.PAYMENTS for _ in s.take(pattern)]
    online = bool(list(s.take(L.CHANNEL_ONLINE)))
    store = bool(list(s.take(L.CHANNEL_STORE)))
    if online and store:
        channel_group, online, store = True, False, False

    # métricas explícitas y preguntas de estado
    strong = {metric for metric, pattern in L.METRIC_STRONG for _ in s.take(pattern)}
    status = bool(list(s.take(L.STATUS)))
    if len(strong) > 1:
        return None
    metric = strong.pop() if strong else None

    # métricas débiles: "ventas", "vendidos", "cuanto vendimos"
    weak_units = bool(list(s.take(L.WEAK_UNITS)))
    weak_revenue = bool(list(s.take(L.WEAK_REVENUE)))

    # sustantivos de dimensión sueltos: entidad del ranking o agrupación
    entity, entity_plural, candidates, noun_groups = None, False, [], 0
    if kind in STOCK_KINDS or kind == "movements":
        for i, tok in enumerate(s.toks):
            if L.PRODUCT_NOUN.fullmatch(tok):
                if _names_unknown(s.toks, i):
                    return None  # "inventario del producto Zapatilla X": no existe
                s.toks[i] = "_"
    for m, i in s.take(L.CANDIDATE):
        word = m.group(0)
        dim = "customer" if word.startswith("quien") else _dim(word)
        if any(c[1] == dim for c in candidates):
            continue  # "quienes son los clientes que mas compran": la misma entidad dos veces
        if dim in ("branch", "product", "category") and _names_unknown(s.toks, i):
            return None
        candidates.append((i, dim, _is_plural(word)))
        if not _is_plural(word):
            s.toks[i] = "_n"  # un sustantivo singular suelto no hace de una cláusula un pedido
    if ranking:
        if len(candidates) > 1:
            return None
        if candidates:
            _, entity, entity_plural = candidates[0]
    else:
        for i, dim, plural in candidates:
            if dim in TIME_DIMENSIONS or not plural:
                return None  # "ventas de los dias", "cuanto vendio la sucursal": ¿cuál?
            if dim != "product":
                groups.append((i, dim))
                noun_groups += 1
    groups.sort(key=lambda g: g[0])

    # regla de oro: lo que sobra
    toks = s.toks
    for i, tok in enumerate(toks):
        cls = _classify(tok)
        if cls == "flag":
            return None
        elif tok in ("por", "segun", "cada") and \
                _classify(next((t for t in toks[i + 1:] if t not in L.ARTICLES), "")) in ("unknown", "role"):
            return None  # "ventas por vendedor": agrupación que no existe
        elif cls == "number":
            # un número pegado a palabras desconocidas es parte de un nombre ("Product 1 active"); si no, ¿qué es?
            near = [toks[j] for j in (i - 1, i + 1) if 0 <= j < len(toks)]
            if not any(_classify(w) == "unknown" for w in near):
                return None
    # dos sucursales (o productos) nombradas y comparadas: "la sur vende más que la del alto" -> agrupar por ellas
    named_pair = next((dim for dim in ("branch", "product", "category") if len(found[dim]) >= 2), None)
    if named_pair and entity is None and not groups and (pair_cue or markers):
        entity, entity_plural, order, top_n, sold, ranking = named_pair, True, order or "desc", None, False, True
        if not explicit_target:
            markers = []  # "la sur vs el alto (este mes)": se comparan sucursales, no períodos
    if not _anchored(words, kind, metric, status, ranking, weak_units or weak_revenue, candidates, found,
                     len(groups) - noun_groups, channel_group or payment_group or compared_entities, period, sold,
                     online or store):
        return None

    return _resolve(kind, metric, status, used_metric, weak_units or sold, weak_revenue, ranking, order, singular or asks_one,
                    top_n, entity, entity_plural, [d for _, d in groups], channel_group, online, store, payments,
                    period, bool(markers) and explicit_target, found)


def _resolve(kind, metric, status, used_metric, weak_units, weak_revenue, ranking, order, singular, top_n,
             entity, entity_plural, groups, channel_group, online, store, payments, period, compare, found):
    group_by: list[str] = []
    for dim in groups + (["channel"] if channel_group else []):
        if dim not in group_by:
            group_by.append(dim)

    if kind != SALES_KIND:
        if ranking or payments or compare or metric in ("revenue", "orders", "avg_ticket", "customers") or \
                weak_revenue or online or store or channel_group:
            return None  # el reporte de stock/movimientos no sabe filtrar por eso
        if kind in STOCK_KINDS and period is not None and period.preset != "today":
            return None  # foto actual del stock: no hay stock "de octubre"
        if set(group_by) - {"branch", "product"}:
            return None  # "inventario por talla", "movimientos diarios": esos reportes no se pueden desglosar así
        # el reporte de stock/movimientos ya lista producto y sucursal: group_by fijo (igual que el reinicio de Groq)
        return _query(kind=kind, group_by=["product"], period=period, found=found)

    entity_named = entity is not None
    if ranking:
        if entity is None:
            if weak_units or not group_by:  # (weak_units incluye "lo más vendido")
                entity = "product"  # "los más vendidos (por sucursal)"
            else:
                entity = group_by.pop()  # "ranking por sucursal"
        if entity in group_by:
            group_by.remove(entity)
        group_by.append(entity)  # [X, E]: el top se calcula dentro de cada X
        if top_n is None and (singular or entity_named and not entity_plural):
            top_n = 1  # "la peor sucursal", "el mas vendido"; "los mas vendidos" no lleva top
        if entity in ("payment_method", "channel"):  # "el método de pago más usado" = más veces, no más plata
            metric = metric or used_metric
        metric = metric or ("units" if entity in UNITS_DIMS else "revenue")
    if len(group_by) > 2 or len(TIME_DIMENSIONS & set(group_by)) > 1:
        return None
    if metric is None:
        if weak_units:
            metric = "units"
        elif weak_revenue or status or payments or not group_by:
            metric = "revenue"
        else:
            metric = "units" if group_by[0] in UNITS_DIMS else "revenue"
    if not group_by and metric == "customers":
        group_by = []  # "cuántos clientes compraron este mes": un solo total
    elif not group_by:
        # sin agrupación dicha: dinero/pedidos/ticket con período -> evolución diaria; si no, por producto
        group_by = ["day"] if metric != "units" and (period is not None or metric != "revenue") else ["product"]
    return _query(kind=kind, metric=metric, group_by=group_by, top_n=top_n, order=order or "desc", period=period,
                  found=found, channel="online" if online else "store" if store else "all",
                  payment_methods=list(dict.fromkeys(payments)), compare_previous=compare)


def _query(found, period, **fields) -> AnalyticsQuery:
    return AnalyticsQuery(
        period=period or PeriodSpec(preset="last_n_days", n=30),
        branch_ids=found["branch"], product_ids=found["product"], category_ids=found["category"], **fields)
