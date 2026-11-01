"""Corrección conservadora de errores de tipeo o del dictado ("ventass", "vendimoz", "bendido", "meces", "pasao").

Se aplica solo a palabras que el intérprete NO pudo usar. Una palabra se corrige si:
- su clave fonética (b=v, z=s=c(e/i), sin h, sin letras dobles, "-ado/-ido" final = "-ao/-io") coincide con la de
  UNA sola palabra conocida; o
- está a distancia de Damerau-Levenshtein 1 (2 si la palabra conocida tiene 9+ letras) de UNA sola palabra conocida
  de 5+ letras.
Empates o palabras cortas (< 4 letras) -> no se corrige (queda como desconocida y actúa la regla de oro / el aviso).
"""
import re
from functools import lru_cache


def phonetic_key(word: str) -> str:
    w = re.sub(r"c(?=[ei])", "s", word).replace("z", "s").replace("v", "b").replace("h", "").replace("ll", "y")
    w = re.sub(r"ck|qu|c|k", "k", w)  # "stok" ~ "stock"
    w = re.sub(r"(.)\1+", r"\1", w)
    return re.sub(r"([ai])d([oa]s?)$", r"\1\2", w)  # "pasado" ~ "pasao"


def distance(a: str, b: str, limit: int) -> int:
    """Damerau-Levenshtein (transposiciones adyacentes); corta en cuanto supera `limit`."""
    if abs(len(a) - len(b)) > limit:
        return limit + 1
    prev2, prev = None, list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        cur = [i] + [0] * len(b)
        for j in range(1, len(b) + 1):
            cost = a[i - 1] != b[j - 1]
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                cur[j] = min(cur[j], prev2[j - 2] + 1)
        if min(cur) > limit:
            return limit + 1
        prev2, prev = prev, cur
    return prev[-1]


# Palabras reales que se parecen a vocabulario del reporte y NO son tipeos ("contador" no es "contado").
ROLE_NOUN = re.compile(r"\w{3,}(?:dor|dora|dores|doras|ista|istas|ente|entes)|\w{4,}(?:ero|era|eros|eras)|"
                       r"cajer[oa]s?|gerentes?|duen[oa]s?|soci[oa]s?|encargad[oa]s?|emplead[oa]s?|jef[ae]s?|"
                       r"cuentas?|ventanas?|tardes?|cartas?|cuenta")


def _is_real_word(word: str) -> bool:
    return bool(ROLE_NOUN.fullmatch(word))


def _edit_allowed(word: str, candidate: str) -> bool:
    """Nunca se agregan ni quitan terminaciones: una letra de más o de menos solo en el MEDIO de la palabra
    (misma primera y última letra). Para palabras que cambian el reporte (pago, canal, tipo, métrica) solo se
    aceptan cambios de letra o transposiciones, salvo en palabras largas (9+ letras: "inventaro")."""
    from app.services.report_language.lexicon import FUZZY_HIGH_IMPACT
    if candidate in FUZZY_HIGH_IMPACT and word[0] != candidate[0]:
        return False  # "renta", "lentas", "afectivo": no se cambia la primera letra de una palabra que cambia el reporte
    if word[-1] != candidate[-1]:  # "contada"/"contador" no son "contado": la terminación no se toca,
        return word[:-2] == candidate[:-2] and word[-2:] == candidate[-2:][::-1]  # salvo letras cruzadas ("florla")
    if len(word) == len(candidate):
        return True
    if word[0] != candidate[0]:
        return False
    return candidate not in FUZZY_HIGH_IMPACT or len(candidate) >= 9


class Corrector:
    def __init__(self, vocab):
        self.vocab = frozenset(vocab)
        self.by_key: dict[str, set] = {}
        self.by_len: dict[int, list] = {}
        for word in self.vocab:
            self.by_key.setdefault(phonetic_key(word), set()).add(word)
            if len(word) >= 5:
                self.by_len.setdefault(len(word), []).append(word)

    def correct(self, word: str) -> str | None:
        if len(word) < 2 or word in self.vocab or not word.isalpha() or _is_real_word(word):
            return None
        same = self.by_key.get(phonetic_key(word), set())
        if same:  # suena igual ("bendido", "oy"); si varias suenan igual, la más cercana letra a letra, sin empate
            ranked = sorted((distance(word, c, 3), c) for c in same)
            return ranked[0][1] if len(ranked) == 1 or ranked[0][0] < ranked[1][0] else None
        if len(word) < 4:
            return None  # palabra corta: solo se corrige si suena exactamente igual
        best, found = 3, set()
        for size in range(len(word) - 2, len(word) + 3):
            for candidate in self.by_len.get(size, ()):
                if not _edit_allowed(word, candidate):
                    continue
                limit = 2 if len(candidate) >= 9 else 1
                d = distance(word, candidate, limit)
                if d <= limit and d < best:
                    best, found = d, {candidate}
                elif d <= limit and d == best:
                    found.add(candidate)
        return next(iter(found)) if len(found) == 1 else None


@lru_cache(maxsize=256)
def corrector_for(extra: frozenset) -> Corrector:
    from app.services.report_language.lexicon import FUZZY_VOCAB
    return Corrector(FUZZY_VOCAB | extra)
