from datetime import date
from uuid import uuid4

import pytest

from app.services.report_interpreter import Catalog, interpret_locally, normalize

ZONA_SUR, LA_PAZ, BLUSA, JEAN, BLUSAS, JEANS = (uuid4() for _ in range(6))
CATALOG = Catalog(
    branches={"ayni zona sur": ZONA_SUR, "ayni la paz centro": LA_PAZ},
    products={"blusa floral": BLUSA, "jean clasico": JEAN},
    categories={"blusas": BLUSAS, "jeans": JEANS},
)

ENGINEER = dict(metric="units", group_by=["branch", "product"], top_n=10, period=("last_n_months", 3))


@pytest.mark.parametrize("text, expected", [
    ("Mostrar los 10 productos más vendidos durante los últimos 3 meses agrupados por sucursal", ENGINEER),
    ("mostrar los diez productos mas vendidos durante los ultimos tres meses agrupados por sucursal", ENGINEER),
    ("top diez productos mas vendidos ultimos tres meses por sucursal", ENGINEER),
    ("ingresos por mes este año", dict(metric="revenue", group_by=["month"], period=("this_year", None))),
    ("ticket promedio por sucursal el mes pasado comparado con el anterior",
     dict(metric="avg_ticket", group_by=["branch"], period=("last_month", None), compare_previous=True)),
    ("ventas online vs tienda de esta semana",
     dict(group_by=["channel"], period=("this_week", None), channel="all", compare_previous=False)),
    ("los 5 productos menos vendidos en Ayni Zona Sur",
     dict(top_n=5, order="asc", branch_ids=[ZONA_SUR], group_by=["product"])),
    ("ventas por talla de la categoria Blusas", dict(group_by=["size"], category_ids=[BLUSAS])),
    ("ventas por mes del ultimo trimestre", dict(group_by=["month"], period=("last_n_months", 3))),
    ("cuanto se vendio hoy", dict(metric="revenue", group_by=["day"], period=("today", None))),
    ("productos por categoria", dict(group_by=["category"], period=("last_n_days", 30))),
    ("pedidos por metodo de pago ayer", dict(metric="orders", group_by=["payment_method"], period=("yesterday", None))),
    ("ingresos online por semana de los ultimos 45 dias", dict(channel="online", group_by=["week"])),
    ("unidades por color en tienda este mes", dict(group_by=["color"], channel="store", period=("this_month", None))),
    ("ingresos por dia del 01/10/2026 al 15/10/2026", dict(group_by=["day"])),
    # el nombre mas largo gana y una sucursal no se vuelve producto/categoria
    ("ventas de Blusa Floral en Ayni La Paz Centro por mes",
     dict(product_ids=[BLUSA], branch_ids=[LA_PAZ], category_ids=[], group_by=["month"])),
])
def test_local_interpreter_phrases(text, expected):
    q = interpret_locally(text, CATALOG)
    assert q is not None
    for field, value in expected.items():
        if field == "period":
            assert (q.period.preset, q.period.n) == value
        else:
            assert getattr(q, field) == value, field


@pytest.mark.parametrize("text, metric, group_by, preset, channel", [
    ("ventas de hoy", "revenue", ["day"], "today", "all"),
    ("ventas del mes pasado", "revenue", ["day"], "last_month", "all"),
    ("ventas web hoy", "revenue", ["day"], "today", "online"),
    ("quiero ver las ventas", "revenue", ["product"], "last_n_days", "all"),
])
def test_bare_sales_question_means_revenue(text, metric, group_by, preset, channel):
    q = interpret_locally(text, CATALOG)
    assert (q.metric, q.group_by, q.period.preset, q.channel) == (metric, group_by, preset, channel)


def test_hola_returns_none():
    assert interpret_locally("hola", CATALOG) is None


def test_custom_dates():
    q = interpret_locally("ingresos por dia del 01/10/2026 al 15/10/2026", CATALOG)
    assert (q.period.preset, q.period.from_date, q.period.to_date) == (
        "custom", date(2026, 10, 1), date(2026, 10, 15))


def test_long_day_range_becomes_custom():
    q = interpret_locally("ingresos de los ultimos 90 dias", CATALOG)  # PeriodSpec.n <= 36
    assert q.period.preset == "custom"
    assert (q.period.to_date - q.period.from_date).days == 89


def test_normalize():
    assert normalize("  ¿Cuántas  VENTAS, año 2026?  ") == "cuantas ventas ano 2026"
    assert normalize("del 01/10/2026") == "del 01/10/2026"


def test_unknown_phrase_returns_none():
    assert interpret_locally("haz un poema sobre ropa", CATALOG) is None


@pytest.mark.parametrize("text", [
    "ventas ultimos 99999999999999999999 dias",
    "ultimos 5000000 dias ingresos",
    "ventas ultimos 99999999999999999999 meses",
    "top 99999999999999999999 productos",
    "ingresos ultimos " + "9" * 5000 + " dias",
])
def test_huge_numbers_never_raise(text):
    q = interpret_locally(text, CATALOG)
    assert q is None or isinstance(q.period.preset, str)


def test_top_and_months_are_clamped():
    assert interpret_locally("top 500 productos", CATALOG).top_n == 50
    q = interpret_locally("ingresos de los ultimos 60 meses", CATALOG)
    assert (q.period.preset, q.period.n) == ("last_n_months", 36)


def test_reversed_range_is_swapped():
    q = interpret_locally("ingresos del 30/09/2026 al 01/09/2026", CATALOG)
    assert (q.period.from_date, q.period.to_date) == (date(2026, 9, 1), date(2026, 9, 30))


def test_invalid_date_returns_none():
    # Regla de oro: una fecha reconocida que no existe no se reemplaza en silencio por "últimos 30 días".
    assert interpret_locally("ingresos del 31/02/2026 al 05/03/2026", CATALOG) is None


def test_longest_catalog_name_wins_over_substring():
    cat = Catalog(products={"blusa": BLUSAS, "blusa floral": BLUSA})
    q = interpret_locally("ventas de blusa floral por mes", cat)
    assert q.product_ids == [BLUSA]
    assert interpret_locally("ventas de blusa por mes", cat).product_ids == [BLUSAS]


# ---------------------------------------------------------------------------------------------------------
# Paráfrasis propias (distintas del corpus dev), con fecha fija: hoy = miércoles 11/11/2026.
# ---------------------------------------------------------------------------------------------------------
import random  # noqa: E402
import time  # noqa: E402

from tests.corpus_eval import TODAY, build_catalog  # noqa: E402

FULL_CATALOG, NAME_BY_ID = build_catalog()
D = date
ID_FIELDS = {"branches": "branch_ids", "products": "product_ids", "categories": "category_ids"}


def ask(text):
    return interpret_locally(text, FULL_CATALOG, today=TODAY)


def check(q, expected):
    assert q is not None, "devolvió None"
    for key, value in expected.items():
        if key == "period":
            assert (q.period.preset, q.period.n) == value, key
        elif key == "custom":
            assert (q.period.preset, q.period.from_date, q.period.to_date) == ("custom", *value), key
        elif key in ID_FIELDS:
            assert sorted(NAME_BY_ID[i] for i in getattr(q, ID_FIELDS[key])) == sorted(value), key
        elif key == "payment_methods":
            assert sorted(q.payment_methods) == sorted(value), key
        else:
            assert getattr(q, key) == value, key


OCT, SEP = (D(2026, 10, 1), D(2026, 10, 31)), (D(2026, 9, 1), D(2026, 9, 30))
PARAPHRASES = [
    # tiempo relativo, meses, rangos, días de la semana
    ("cuanto facturo la sucursal de cochabamba la semana pasada",
     dict(metric="revenue", period=("last_week", None), branches=["Ayni Cochabamba"])),
    ("y hoy cuanto llevamos", dict(metric="revenue", period=("today", None))),
    ("quiero saber las ventas del dia de hoy", dict(metric="revenue", period=("today", None))),
    ("reporte de ingresos de los ultimos doce meses", dict(metric="revenue", period=("last_n_months", 12))),
    ("ingresos de las ultimas dos semanas", dict(metric="revenue", period=("last_n_days", 14))),
    ("ventas en lo que va de la semana", dict(period=("this_week", None))),
    ("dame un resumen de las ventas de la semana", dict(period=("this_week", None))),
    ("cuanto vendimos el miercoles", dict(custom=(D(2026, 11, 11), D(2026, 11, 11)))),
    ("ventas del jueves pasado", dict(custom=(D(2026, 11, 5), D(2026, 11, 5)))),
    ("cuanto vendimos anteayer", dict(metric="revenue", custom=(D(2026, 11, 9), D(2026, 11, 9)))),
    ("que tal estuvo el lunes", dict(metric="revenue", custom=(D(2026, 11, 9), D(2026, 11, 9)))),
    ("ventas de noviembre", dict(custom=(D(2026, 11, 1), D(2026, 11, 30)))),
    ("ventas de noviembre de dos mil veinticinco", dict(custom=(D(2025, 11, 1), D(2025, 11, 30)))),
    ("ventas de diciembre de este ano", dict(custom=(D(2026, 12, 1), D(2026, 12, 31)))),
    ("ventas de agosto del ano pasado", dict(custom=(D(2025, 8, 1), D(2025, 8, 31)))),
    ("del 20 de octubre al 3 de noviembre cuanto vendimos",
     dict(metric="revenue", custom=(D(2026, 10, 20), D(2026, 11, 3)))),
    ("ventas del 15/09 al 15/10", dict(custom=(D(2026, 9, 15), D(2026, 10, 15)))),
    ("ventas del primero al diez de octubre", dict(custom=(D(2026, 10, 1), D(2026, 10, 10)))),
    ("ventas del primer trimestre", dict(custom=(D(2026, 1, 1), D(2026, 3, 31)))),
    ("ventas de la gestion pasada", dict(period=("last_year", None))),
    ("ventas de esta gestion", dict(period=("this_year", None))),
    ("cuanto vendimos la ultima semana", dict(period=("last_n_days", 7))),
    ("VENTAS POR SUCURSAL DEL MES PASADO", dict(metric="revenue", group_by=["branch"], period=("last_month", None))),
    ("ventas, por favor, de ayer!!!", dict(metric="revenue", period=("yesterday", None))),
    ("Oye, ¿cuánto hemos facturado en la sucursal de El Alto durante este mes?",
     dict(metric="revenue", period=("this_month", None), branches=["Ayni El Alto"])),
    # métricas
    ("cuanta plata se hizo ayer en la tienda fisica", dict(metric="revenue", channel="store")),
    ("que tanto vendimos ayer", dict(metric="revenue", period=("yesterday", None))),
    ("cuantas poleras se vendieron ayer", dict(metric="units", categories=["Poleras"])),
    ("cuantas faldas vendimos en la zona sur el mes pasado",
     dict(metric="units", categories=["Faldas"], branches=["Ayni Zona Sur"], period=("last_month", None))),
    ("cantidad de pedidos online por semana", dict(metric="orders", group_by=["week"], channel="online")),
    ("ticket promedio online", dict(metric="avg_ticket", channel="online")),
    ("gasto promedio por cliente", dict(metric="avg_ticket", group_by=["customer"])),
    ("el promedio de compra en tienda", dict(metric="avg_ticket", channel="store")),
    ("cuantos clientes distintos compraron por internet", dict(metric="customers", channel="online")),
    ("cuantos clientes compraron en octubre por sucursal",
     dict(metric="customers", group_by=["branch"], custom=OCT)),
    ("como nos fue en el alto este mes", dict(metric="revenue", branches=["Ayni El Alto"])),
    # rankings
    ("cual fue la prenda mas vendida en septiembre",
     dict(group_by=["product"], metric="units", top_n=1, order="desc", custom=SEP)),
    ("las cinco prendas mas vendidas", dict(group_by=["product"], metric="units", top_n=5)),
    ("que talla se vende menos en el alto",
     dict(group_by=["size"], metric="units", top_n=1, order="asc", branches=["Ayni El Alto"])),
    ("los tres colores mas vendidos de la categoria jeans",
     dict(group_by=["color"], top_n=3, categories=["Jeans"])),
    ("cual es el producto estrella", dict(group_by=["product"], top_n=1, order="desc")),
    ("cual es la mejor sucursal este ano", dict(group_by=["branch"], metric="revenue", top_n=1)),
    ("cuales son las sucursales que menos venden",
     dict(group_by=["branch"], metric="revenue", order="asc", top_n=None)),
    ("que sucursal tuvo mas pedidos el mes pasado", dict(group_by=["branch"], metric="orders", top_n=1)),
    ("la sucursal con el ticket promedio mas alto",
     dict(group_by=["branch"], metric="avg_ticket", top_n=1, order="desc", branches=[])),
    ("el metodo de pago menos usado este mes",
     dict(group_by=["payment_method"], metric="orders", top_n=1, order="asc")),
    ("cual es la forma de pago mas usada en el alto",
     dict(group_by=["payment_method"], metric="orders", top_n=1, branches=["Ayni El Alto"])),
    ("el color mas popular", dict(group_by=["color"], metric="units", top_n=1)),
    ("quiero ver el top diez de productos", dict(group_by=["product"], top_n=10)),
    ("dame el top de productos de octubre", dict(group_by=["product"], top_n=None, custom=OCT)),
    ("cuales fueron los treinta y cinco productos mas vendidos", dict(top_n=35)),
    ("los productos que mas se venden en la zona sur",
     dict(group_by=["product"], metric="units", branches=["Ayni Zona Sur"])),
    ("lo menos vendido por categoria", dict(group_by=["category", "product"], order="asc", metric="units")),
    ("las prendas menos vendidas del mes pasado por sucursal",
     dict(group_by=["branch", "product"], order="asc", period=("last_month", None))),
    ("dime los 3 productos mas vendidos en cada sucursal", dict(group_by=["branch", "product"], top_n=3)),
    ("en que dia se vendio mas", dict(group_by=["day"], metric="revenue", top_n=1)),
    ("el mejor mes del ano", dict(group_by=["month"], top_n=1, period=("this_year", None))),
    ("cual fue nuestro peor mes del ano", dict(group_by=["month"], top_n=1, order="asc")),
    ("la semana con mas ventas del trimestre", dict(group_by=["week"], top_n=1, period=("this_quarter", None))),
    ("en que sucursal vendimos menos el trimestre pasado",
     dict(group_by=["branch"], order="asc", top_n=1, period=("last_quarter", None))),
    ("en que sucursal se vende mas jean clasico",
     dict(group_by=["branch"], metric="revenue", top_n=1, products=["Jean Clasico"])),
    ("cual es la categoria con mas ingresos", dict(group_by=["category"], metric="revenue", top_n=1)),
    ("la peor categoria del ano pasado", dict(group_by=["category"], metric="units", order="asc", top_n=1)),
    # clientes
    ("quienes son los clientes que mas compran", dict(group_by=["customer"], metric="revenue", top_n=None)),
    ("quien es el cliente que mas gasto", dict(group_by=["customer"], metric="revenue", top_n=1)),
    ("los veinte mejores clientes", dict(group_by=["customer"], top_n=20)),
    ("top 3 clientes de la sucursal sur", dict(group_by=["customer"], top_n=3, branches=["Ayni Zona Sur"])),
    # agrupaciones
    ("ventas por forma de pago", dict(group_by=["payment_method"], metric="revenue")),
    ("ingresos segun metodo de pago", dict(group_by=["payment_method"])),
    ("pedidos por canal este ano", dict(group_by=["channel"], metric="orders")),
    ("ingresos mensuales por sucursal", dict(group_by=["month", "branch"])),
    ("ventas por metodo de pago y por sucursal", dict(group_by=["payment_method", "branch"])),
    ("ingresos semanales del mes pasado", dict(group_by=["week"], period=("last_month", None))),
    ("mmm a ver muestrame las ventas de la semana pasada por dia",
     dict(group_by=["day"], period=("last_week", None))),
    ("a ver las ventas por sucursal de este mes", dict(group_by=["branch"], period=("this_month", None))),
    # canal y pago
    ("ventas en linea vs presenciales", dict(group_by=["channel"], channel="all", compare_previous=False)),
    ("compara online y tienda fisica", dict(group_by=["channel"], compare_previous=False)),
    ("ventas presenciales de ayer", dict(channel="store", period=("yesterday", None))),
    ("cuanto se vendio en la app", dict(channel="online", metric="revenue")),
    ("pagos en efectivo de la semana pasada", dict(payment_methods=["cash"], metric="revenue")),
    ("cuanto cobramos con qr hoy", dict(payment_methods=["qr"], metric="revenue", period=("today", None))),
    ("ventas con billetera digital", dict(payment_methods=["wallet"])),
    ("cuanto vendimos con qr y con tarjeta este mes", dict(payment_methods=["qr", "card"])),
    # comparaciones
    ("comparame las ventas con el periodo anterior", dict(compare_previous=True)),
    ("compara las ventas de este mes con el anterior",
     dict(compare_previous=True, period=("this_month", None))),
    ("ventas del trimestre comparadas con el trimestre anterior",
     dict(compare_previous=True, period=("this_quarter", None))),
    # catálogo
    ("ventas de blusas y jeans", dict(categories=["Blusas", "Jeans"])),
    ("ventas de vestidos en el centro y en el alto",
     dict(categories=["Vestidos"], branches=["Ayni La Paz Centro", "Ayni El Alto"])),
    ("eh este muestrame cuanto se vendio pues en la sucursal del alto",
     dict(metric="revenue", branches=["Ayni El Alto"])),
    # inventario, stock crítico y movimientos
    ("stock de blusa floral por sucursal", dict(kind="inventory", group_by=["product"], products=["Blusa Floral"])),
    ("cuanto stock queda de falda plisada en el centro",
     dict(kind="inventory", products=["Falda Plisada"], branches=["Ayni La Paz Centro"])),
    ("productos sin stock por sucursal", dict(kind="critical_stock", group_by=["product"])),
    ("que prendas se estan acabando", dict(kind="critical_stock")),
    ("movimientos de inventario del centro esta semana",
     dict(kind="movements", branches=["Ayni La Paz Centro"], period=("this_week", None))),
    ("reposiciones de jeans en septiembre", dict(kind="movements", categories=["Jeans"], custom=SEP)),
    ("cuantas reposiciones hubo ayer", dict(kind="movements", period=("yesterday", None))),
]


@pytest.mark.parametrize("text, expected", PARAPHRASES, ids=[t for t, _ in PARAPHRASES])
def test_paraphrases(text, expected):
    check(ask(text), expected)


NO_SILENT_GUESS = [
    # nombres o dimensiones que no existen
    "ventas de la sucursal norte", "cuanto vendio la sucursal norte", "ventas por vendedor",
    "ventas por empleado este mes", "ventas por marca", "ventas por hora",
    # métricas sin datos o que no son lo que parecen
    "ventas netas", "el promedio de ventas por dia", "crecimiento de ventas", "porcentaje de ventas online",
    "proyeccion de ventas para diciembre", "devoluciones del mes", "descuentos aplicados este mes",
    "cuanto ganamos este mes", "pedidos cancelados de hoy", "pedidos pendientes",
    # pagos y canales no soportados o negados
    "ventas a credito", "pagos por transferencia este mes", "ventas sin tarjeta", "ventas que no sean online",
    "ventas excepto efectivo",
    # tiempo que no sabemos resolver
    "ventas del mes que viene", "ventas de manana", "ventas de la proxima semana", "ventas de hace un mes",
    "ventas de la ultima quincena", "ventas del dia del padre", "ventas de black friday", "ventas de fin de mes",
    "ventas en la tarde", "ventas de los sabados", "ventas de mediados de octubre", "ventas desde octubre",
    "ventas hasta ayer", "ventas del 31 de septiembre", "ventas del 1/13/2026 al 5/13/2026",
    "ventas entre octubre y noviembre", "ventas de 15 dias", "ventas 15", "cuanto vendimos ayer y hoy",
    "ventas de este mes vs el mismo mes del ano pasado", "inventario de octubre",
    # combinaciones imposibles o contradictorias
    "ventas por sucursal por categoria y por mes", "los productos mas vendidos y los menos vendidos",
    "inventario mas alto",
    # no son reportes de ventas
    "cuantas sucursales tenemos", "cuantas categorias hay", "lista de clientes", "clientes nuevos este mes",
    "clientes frecuentes", "cuanto cuesta la blusa floral", "que puedes hacer", "lo mismo de antes",
    "cuanto es dos mas dos", "y en el alto", "borra las ventas de ayer", "buenas tardes", "gracias eso es todo",
]


@pytest.mark.parametrize("text", NO_SILENT_GUESS)
def test_no_silent_guess(text):
    assert ask(text) is None


def test_today_is_injectable():
    q = interpret_locally("ventas de octubre", FULL_CATALOG, today=D(2026, 9, 15))  # octubre aún no llega
    assert (q.period.from_date, q.period.to_date) == (D(2025, 10, 1), D(2025, 10, 31))
    q = interpret_locally("ventas del lunes", FULL_CATALOG, today=D(2026, 11, 16))  # hoy es lunes -> hoy
    assert q.period.from_date == D(2026, 11, 16)


def test_adversarial_input_is_fast():
    texts = [
        "de " * 166, "por " * 125, "cuantos " + "x " * 240 + "vendimos", "del 1/1 al " * 45,
        "ventas " + "mas menos " * 50, "a" * 500, "mes de " * 80, "y por sucursal " * 30, "1/" * 250,
        "ventas del 1 al 2 de octubre " * 17, "cuantas " * 60 + "vendimos", "sucursal " * 55 + "sur",
    ]
    for text in texts:
        start = time.perf_counter()
        ask(text[:500])
        assert time.perf_counter() - start < 0.5, text[:40]


def test_no_exception_escapes_for_random_strings():
    rng = random.Random(20261111)
    alphabet = "abcdefghijklmnopqrstuvwxyz áéíóúñ¿?¡!/0123456789‮\u0000\U0001f600-.,"
    words = ("ventas por sucursal top 5 del al de octubre ultimos dias mas menos vs comparado / 31 "
             "99999999999 primero 0/0 13/13/0000 y cada stock sin").split()
    for _ in range(400):
        if rng.random() < 0.5:
            text = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 600)))
        else:
            text = " ".join(rng.choice(words) for _ in range(rng.randint(0, 120)))
        result = interpret_locally(text, FULL_CATALOG, today=TODAY)
        assert result is None or result.period is not None


# ---------------------------------------------------------------------------------------------------------
# Ronda de correcciones 1
# ---------------------------------------------------------------------------------------------------------
from app.services.report_interpreter import interpret_locally_detailed  # noqa: E402

LAST_3_MONTHS = ("last_n_months", 3)
GENERALIZATION = [
    # dos períodos en una comparación: el primero es el pedido, el segundo la referencia
    ("compara las ventas de este mes con las del mes pasado",
     dict(metric="revenue", period=("this_month", None), compare_previous=True)),
    ("las ventas de hoy contra las de ayer", dict(period=("today", None), compare_previous=True)),
    ("ingresos de esta semana frente a la semana pasada", dict(period=("this_week", None), compare_previous=True)),
    ("compara las ventas de octubre con septiembre", dict(custom=OCT, compare_previous=True)),
    ("ventas de octubre vs septiembre", dict(custom=OCT, compare_previous=True)),
    # la entidad antes del interrogativo singular: top 1
    ("de todas las sucursales cual vendio mas este mes",
     dict(group_by=["branch"], metric="revenue", top_n=1, order="desc", period=("this_month", None))),
    ("entre los productos cual se vende menos", dict(group_by=["product"], metric="units", top_n=1, order="asc")),
    ("de los colores cual se vendio mas", dict(group_by=["color"], top_n=1, order="desc")),
    # verbos de "vender" menos comunes, en contexto de unidades
    ("en el ultimo trimestre cuantas prendas salieron", dict(metric="units", period=LAST_3_MONTHS)),
    ("que producto se movio mas esta semana", dict(group_by=["product"], metric="units", top_n=1, order="desc")),
    ("que talla roto menos", dict(group_by=["size"], metric="units", top_n=1, order="asc")),
    ("cuantas unidades se despacharon ayer", dict(metric="units", period=("yesterday", None))),
    ("cuantos jeans se fueron esta semana", dict(metric="units", categories=["Jeans"])),
    ("cuantas blusas se llevaron hoy", dict(metric="units", categories=["Blusas"], period=("today", None))),
    # errores de tipeo o del dictado (distancia 1; 2 solo en palabras de 9+ letras)
    ("ventass de hoy", dict(metric="revenue", period=("today", None))),
    ("cuanto vendimoz ayer", dict(metric="revenue", period=("yesterday", None))),
    ("ventas de la sucurzal sur", dict(metric="revenue", branches=["Ayni Zona Sur"])),
    ("los productos mas vendidoz", dict(group_by=["product"], metric="units", order="desc")),
    ("inventaro", dict(kind="inventory")),
    ("stok critico", dict(kind="critical_stock")),
    ("clientez que mas compran", dict(group_by=["customer"], metric="revenue")),
    ("ventas de cochabamaba", dict(branches=["Ayni Cochabamba"])),
    ("ventas de la blusa florla", dict(products=["Blusa Floral"])),
    ("ventas de setiembre", dict(custom=SEP)),
]


@pytest.mark.parametrize("text, expected", GENERALIZATION, ids=[t for t, _ in GENERALIZATION])
def test_generalization_round_1(text, expected):
    check(ask(text), expected)


@pytest.mark.parametrize("text", [
    "ventas de hoy vs octubre del ano pasado",  # la referencia no es el período anterior
    "compara este mes con el mismo mes del ano pasado",
])
def test_comparisons_with_a_baseline_that_is_not_previous_return_none(text):
    assert ask(text) is None


def test_fuzzy_is_conservative():
    assert ask("ventas de marso").period.from_date == D(2026, 3, 1)  # distancia 1 solo a 'marzo'
    assert ask("ventas de hoi") is None or ask("ventas de hoi").period.preset != "today"  # palabra corta: no se corrige
    q, ignored = interpret_locally_detailed("ventas de juxio", FULL_CATALOG, today=TODAY)  # julio/junio empatan
    assert q is None or "juxio" in ignored


IGNORED = [
    ("ventas de zapatos", ["zapatos"]),
    ("ventas de zapatos y carteras este mes", ["zapatos", "carteras"]),
    ("eh oye por favor dame las ventas de hoy gracias", []),
    ("buenas tardes quiero que me muestres el reporte de ventas del mes pasado por favor", []),
    ("Mostrar los 10 productos más vendidos durante los últimos 3 meses agrupados por sucursal", []),
    ("tickets emitidos este mes", []),
    ("mostrame el inventario", []),
]


@pytest.mark.parametrize("text, ignored", IGNORED)
def test_ignored_words_are_reported(text, ignored):
    q, words = interpret_locally_detailed(text, FULL_CATALOG, today=TODAY)
    assert q is not None and words == ignored


def test_ignored_words_are_capped_deduplicated_and_unfiltered_spec_is_kept():
    q, words = interpret_locally_detailed("ventas de zapatos zapatos uno dos tres cuatro aaa bbb ccc ddd eee fff",
                                          FULL_CATALOG, today=TODAY)
    assert q is None or len(words) <= 5
    q, words = interpret_locally_detailed("ventas de zapatos", FULL_CATALOG, today=TODAY)
    assert (q.metric, q.product_ids, q.category_ids, q.branch_ids) == ("revenue", [], [], [])
    assert interpret_locally("ventas de zapatos", FULL_CATALOG, today=TODAY) == q


def test_dev_corpus_ignored_words_never_include_fillers():
    import json
    from pathlib import Path
    fillers = {"por", "favor", "oye", "eh", "dame", "muestrame", "dime", "quiero", "necesito", "reporte", "informe",
               "el", "la", "de", "las", "los", "buenas", "porfa"}
    entries = json.loads((Path(__file__).parent / "data" / "report_phrases_dev.json").read_text(encoding="utf-8"))
    for entry in entries:
        _, words = interpret_locally_detailed(entry["phrase"], FULL_CATALOG, today=TODAY)
        assert not fillers & set(words), (entry["id"], words)


# ---------------------------------------------------------------------------------------------------------
# Frases de sondeo del controlador (expectativas derivadas de las convenciones del plan)
# ---------------------------------------------------------------------------------------------------------
CONTROLLER_PROBE = [
    ("dame las ventas de hoy", dict(kind="sales", metric="revenue", period=("today", None))),
    ("cuanto vendimos hoy", dict(metric="revenue", period=("today", None))),
    ("cuanto vendi ayer", dict(metric="revenue", period=("yesterday", None))),
    ("muestrame las ventas de la semana", dict(metric="revenue", period=("this_week", None))),
    ("quiero ver cuanto se vendio este mes", dict(metric="revenue", period=("this_month", None))),
    ("reporte de ventas", dict(kind="sales", metric="revenue", period=("last_n_days", 30))),
    ("informe de ventas del mes pasado", dict(metric="revenue", period=("last_month", None))),
    ("cual es el producto mas vendido", dict(group_by=["product"], metric="units", top_n=1, order="desc")),
    ("cual es la sucursal que mas vende", dict(group_by=["branch"], metric="revenue", top_n=1, order="desc")),
    ("que sucursal vendio mas este mes",
     dict(group_by=["branch"], metric="revenue", top_n=1, order="desc", period=("this_month", None))),
    ("los productos que menos se venden", dict(group_by=["product"], metric="units", order="asc", top_n=None)),
    ("el mejor producto del mes",
     dict(group_by=["product"], metric="units", top_n=1, order="desc", period=("this_month", None))),
    ("la peor sucursal", dict(group_by=["branch"], metric="revenue", top_n=1, order="asc")),
    ("cuantos pedidos hubo hoy", dict(metric="orders", period=("today", None))),
    ("cuanto facturamos esta semana", dict(metric="revenue", period=("this_week", None))),
    ("cuanta plata entro ayer", dict(metric="revenue", period=("yesterday", None))),
    ("ventas por internet", dict(metric="revenue", channel="online")),
    ("ventas de la tienda fisica", dict(metric="revenue", channel="store")),
    ("ventas en efectivo de hoy", dict(metric="revenue", payment_methods=["cash"], period=("today", None))),
    ("ventas con tarjeta este mes", dict(metric="revenue", payment_methods=["card"], period=("this_month", None))),
    ("ventas por qr", dict(metric="revenue", payment_methods=["qr"])),
    ("ventas de octubre", dict(metric="revenue", custom=OCT)),
    ("ventas del mes de septiembre", dict(metric="revenue", custom=SEP)),
    ("ventas del 1 al 15 de octubre", dict(metric="revenue", custom=(D(2026, 10, 1), D(2026, 10, 15)))),
    ("ventas del año pasado", dict(metric="revenue", period=("last_year", None))),
    ("ventas del ultimo trimestre", dict(metric="revenue", period=("last_n_months", 3))),
    ("ventas de los ultimos quince dias", dict(metric="revenue", period=("last_n_days", 15))),
    ("ventas de la semana pasada", dict(metric="revenue", period=("last_week", None))),
    ("como van las ventas", dict(kind="sales", metric="revenue")),
    ("cuanto llevamos vendido", dict(metric="revenue")),
    ("dime los 3 productos mas vendidos", dict(group_by=["product"], metric="units", top_n=3, order="desc")),
    ("los cinco mejores productos", dict(group_by=["product"], metric="units", top_n=5, order="desc")),
    ("top 5 de blusas",
     dict(group_by=["product"], metric="units", top_n=5, order="desc", categories=["Blusas"])),
    ("ventas de ayer en ayni zona sur",
     dict(metric="revenue", period=("yesterday", None), branches=["Ayni Zona Sur"])),
    ("ventas por talla", dict(group_by=["size"], metric="revenue")),
    ("ventas por color", dict(group_by=["color"], metric="revenue")),
    ("cuanto se vendio en ayni el alto", dict(metric="revenue", branches=["Ayni El Alto"])),
    ("comparame las sucursales", dict(group_by=["branch"], compare_previous=False)),
    ("compara las ventas de este mes con las del mes pasado",
     dict(metric="revenue", period=("this_month", None), compare_previous=True)),
    ("ventas diarias de esta semana", dict(group_by=["day"], metric="revenue", period=("this_week", None))),
    ("ventas por dia", dict(group_by=["day"], metric="revenue")),
    ("ventas semanales del mes", dict(group_by=["week"], metric="revenue", period=("this_month", None))),
    ("mostrame el inventario", dict(kind="inventory")),
    ("que productos tienen poco stock", dict(kind="critical_stock")),
    ("stock critico", dict(kind="critical_stock")),
    ("cuanto stock hay de blusa floral", dict(kind="inventory", products=["Blusa Floral"])),
    ("movimientos de inventario de esta semana", dict(kind="movements", period=("this_week", None))),
    ("mis mejores clientes", dict(kind="sales", group_by=["customer"], metric="revenue", top_n=None)),
    ("cuantos clientes compraron este mes", dict(metric="customers", group_by=[], period=("this_month", None))),
    ("ticket promedio de hoy", dict(metric="avg_ticket", period=("today", None))),
    ("ventas totales", dict(kind="sales", metric="revenue")),
    ("que se vendio mas ayer", dict(group_by=["product"], metric="units", order="desc", period=("yesterday", None))),
]


@pytest.mark.parametrize("text, expected", CONTROLLER_PROBE, ids=[t for t, _ in CONTROLLER_PROBE])
def test_controller_probe_phrases(text, expected):
    q = ask(text)
    check(q, expected)
    if q.kind != "sales":  # los campos solo de ventas quedan en su valor por defecto
        assert (q.metric, q.top_n, q.order, q.channel, q.payment_methods, q.compare_previous) == \
            ("units", None, "desc", "all", [], False)


# ---------------------------------------------------------------------------------------------------------
# Aclaraciones 10-22 (2.ª tanda): voces de personal de tienda, abreviaturas, tipeos, varios reportes a la vez
# ---------------------------------------------------------------------------------------------------------
STAFF_VOICE = [
    # 10: "la tienda del alto" es la sucursal, no el canal
    ("me podrias decir por favor cuanto se vendio en la tienda del alto esta semana",
     dict(metric="revenue", channel="all", branches=["Ayni El Alto"], period=("this_week", None))),
    # 13: dos métodos de pago comparados -> agrupar
    ("efectivo vs tarjeta este mes", dict(group_by=["payment_method"], payment_methods=[], compare_previous=False)),
    ("pagos en efectivo versus qr", dict(group_by=["payment_method"], payment_methods=[])),
    # 15 y 14
    ("mejores clientes del mes", dict(group_by=["customer"], period=("this_month", None))),
    ("las ventas de la ultima semana", dict(period=("last_n_days", 7))),
    # 16: preguntas de estado
    ("que tan bien nos fue ayer", dict(metric="revenue", period=("yesterday", None))),
    ("como estamos de ventas", dict(metric="revenue")),
    ("los numeros de ayer", dict(metric="revenue", period=("yesterday", None))),
    ("el balance del mes", dict(metric="revenue", period=("this_month", None))),
    ("como cerramos el mes pasado", dict(metric="revenue", period=("last_month", None))),
    # 17: dos sucursales nombradas comparadas
    ("la sucursal sur vende mas que la del alto",
     dict(group_by=["branch"], metric="revenue", top_n=None, branches=["Ayni Zona Sur", "Ayni El Alto"])),
    ("ayni zona sur vs ayni el alto este mes",
     dict(group_by=["branch"], compare_previous=False, period=("this_month", None),
          branches=["Ayni Zona Sur", "Ayni El Alto"])),
    # 18: inventario y movimientos
    ("cuanta mercaderia tenemos", dict(kind="inventory")),
    ("cuantas blusas me quedan", dict(kind="inventory", categories=["Blusas"])),
    ("que tengo de jeans en el centro", dict(kind="inventory", categories=["Jeans"], branches=["Ayni La Paz Centro"])),
    ("llego mercaderia esta semana", dict(kind="movements", period=("this_week", None))),
    # 19: verbos de venta en unidades y rotación
    ("lo que salio hoy", dict(metric="units", period=("today", None))),
    ("rotacion de productos del mes", dict(metric="units", group_by=["product"], period=("this_month", None))),
    ("digame cuales son los 5 productos que mas salen", dict(group_by=["product"], metric="units", top_n=5)),
    # 22: abreviaturas de teléfono
    ("vtas de hoy x suc", dict(metric="revenue", group_by=["branch"], period=("today", None))),
    ("q tal las vtas de ayer", dict(metric="revenue", period=("yesterday", None))),
    ("los prods mas vendidos de la semana", dict(group_by=["product"], metric="units", period=("this_week", None))),
    ("ventas de la sucursal sur de ayer xfa tmb", dict(branches=["Ayni Zona Sur"], period=("yesterday", None))),
    ("q prods tienen poco stok", dict(kind="critical_stock")),
    # tipeos y transcripciones: b/v, s/z/c, letras de más o de menos, "-ado" -> "-ao"
    ("cuanto bendimos el mes pasao", dict(metric="revenue", period=("last_month", None))),
    ("ventas de los ultimos tres meces", dict(period=("last_n_months", 3))),
    ("bentas de esta semana", dict(metric="revenue", period=("this_week", None))),
    ("ventaz de ayer", dict(metric="revenue", period=("yesterday", None))),
    ("cuanto se a bendido oy", dict(metric="revenue", period=("today", None))),
    # pedido escondido en una frase larga
    ("hola buenas, disculpe la molestia, me podria ayudar con un dato, necesito saber cuanto se vendio la semana "
     "pasada en total", dict(metric="revenue", period=("last_week", None))),
    ("oye una consulta rapida, de todas las sucursales cual fue la que mas vendio el mes pasado",
     dict(group_by=["branch"], top_n=1, order="desc", period=("last_month", None))),
    ("de septiembre, cuanto facturamos", dict(metric="revenue", custom=SEP)),
    ("cuanto gasto en promedio cada cliente", dict(metric="avg_ticket", group_by=["customer"])),
]


@pytest.mark.parametrize("text, expected", STAFF_VOICE, ids=[t[:60] for t, _ in STAFF_VOICE])
def test_staff_voice(text, expected):
    check(ask(text), expected)


@pytest.mark.parametrize("text", [
    "quisiera saber cuanto vendimos ayer en la tarde", "esta manana cuanto se vendio",  # 12: partes del día
    "cuantos pedidos hubo por la tarde",
    "ventas, stock critico y clientes de todo", "ventas y stock de hoy",  # 20: varios reportes a la vez
    "dime las ventas y el ticket promedio", "cuanto vendimos y cuantos pedidos hubo",
    "cuanto ganamos", "pq bajaron las ventas",  # 21, 22
    "quiero saber si las ventas por internet subieron este mes",  # tendencia: no hay ese reporte
    "ventas de la sucursal santa cruz", "ventas de este mes vs octubre del ano pasado",
])
def test_staff_voice_returns_none(text):
    assert ask(text) is None


@pytest.mark.parametrize("text, words", [
    ("ventas de santa cruz", ["santa", "cruz"]),
    ("ventas de zapatillas deportivas en el centro", ["zapatillas", "deportivas"]),
    ("quisiera saber por favor si me podrias decir las ventas de ayer, gracias", []),
    ("oye una consulta rapida, me podrias pasar las vtas de hoy xfa", []),
])
def test_warnings_only_name_content_words(text, words):
    assert interpret_locally_detailed(text, FULL_CATALOG, today=TODAY)[1] == words


# ---------------------------------------------------------------------------------------------------------
# Ronda de correcciones 2
# ---------------------------------------------------------------------------------------------------------
from app.services.report_language.fuzzy import corrector_for  # noqa: E402


@pytest.mark.parametrize("word", [
    # personas y oficios parecidos a palabras del reporte
    "contador", "contadora", "contadores", "vendedor", "cajero", "cajera", "gerente", "comprador", "administrador",
    "encargado", "dueno", "socio", "proveedor",
    # palabras reales a una letra de distancia de una palabra del reporte
    "cuentas", "ventana", "ventanas", "tarde", "tardes", "carta", "tarjetero",
    # no se agregan ni quitan terminaciones
    "contada", "efectiva", "ventasa",
])
def test_fuzzy_never_turns_a_real_word_into_report_vocabulary(word):
    assert corrector_for(frozenset({"cochabamba", "floral", "plisada"})).correct(word) is None


@pytest.mark.parametrize("text, expected", [
    ("el contador me pidio las ventas con tarjeta de este mes",
     dict(payment_methods=["card"], period=("this_month", None))),
    ("ventas con tarjeta que pidio la contadora", dict(payment_methods=["card"])),
    ("el cajero necesita las ventas en efectivo de ayer", dict(payment_methods=["cash"], period=("yesterday", None))),
    ("el vendedor quiere saber las ventas de hoy", dict(metric="revenue", period=("today", None))),
])
def test_people_mentioned_do_not_change_the_report(text, expected):
    check(ask(text), expected)


@pytest.mark.parametrize("text", [
    "ventas por vendedor", "el mejor vendedor del mes", "ranking de cajeros", "cuanto vendio cada vendedor",
    "quien es el vendedor que mas vende", "ventas por proveedor", "cuentas de ayer", "abre la ventana",
])
def test_people_rankings_and_lookalikes_return_none(text):
    assert ask(text) is None


RAMBLING = [
    ("Buenas tardes, soy doña Rosa, la dueña, la verdad no sé mucho de computadoras, pero dígame cuánto vendimos ayer",
     dict(metric="revenue", period=("yesterday", None))),
    ("mire joven, hace veinte años que tengo la tienda y nunca usé estas cosas, quisiera saber las ventas de la "
     "semana pasada", dict(metric="revenue", period=("last_week", None))),
    ("disculpe la molestia, mi nieto me instaló esto, lo que quiero saber es cuál sucursal vendió más el mes pasado",
     dict(group_by=["branch"], top_n=1, order="desc", period=("last_month", None))),
    ("hola, ya que estamos, me podría decir cuántos pedidos hubo hoy, nada más eso",
     dict(metric="orders", period=("today", None))),
    ("Estimado sistema, por medio de la presente solicito el reporte de ingresos del trimestre pasado por sucursal",
     dict(metric="revenue", group_by=["branch"], period=("last_quarter", None))),
    ("ya pues, dime cuánto entró en efectivo esta semana en el centro, porque el cajero dice que falta plata",
     dict(payment_methods=["cash"], period=("this_week", None), branches=["Ayni La Paz Centro"])),
    ("me acuerdo que el año pasado vendíamos más, pero ahora quiero ver las ventas de este mes",
     dict(metric="revenue", period=("this_month", None))),
    ("cuanto vendimos ayer, aunque no sé si el sistema anda bien", dict(metric="revenue", period=("yesterday", None))),
    ("hola hijita, de todas las sucursales, cuál vendió más este mes",
     dict(group_by=["branch"], top_n=1, period=("this_month", None))),
    ("oiga pues compadre, en el campo no tenemos internet casi, quiero saber cuantas prendas salieron en el alto "
     "la semana pasada", dict(metric="units", branches=["Ayni El Alto"], period=("last_week", None))),
]


@pytest.mark.parametrize("text, expected", RAMBLING, ids=[t[:50] for t, _ in RAMBLING])
def test_rambling_requests_resolve_the_buried_ask(text, expected):
    q, words = interpret_locally_detailed(text, FULL_CATALOG, today=TODAY)
    check(q, expected)
    assert words == []  # la conversación nunca aparece en los avisos


@pytest.mark.parametrize("text", [
    "ventas de hoy, pero sin tarjeta",  # la restricción reconocida no se ignora
    "dame las ventas de hoy, y también el stock crítico",  # dos reportes
    "hola, ventas de la semana, y el inventario de la sucursal sur",
])
def test_rambling_with_a_real_second_ask_or_restriction_returns_none(text):
    assert ask(text) is None


@pytest.mark.parametrize("text, expected", [
    ("ventas de faldas plisadas", dict(products=["Falda Plisada"])),
    ("cuantas falda plisada vendimos", dict(metric="units", products=["Falda Plisada"])),
    ("inventario de poleras basicas", dict(kind="inventory", products=["Polera Basica"])),
    ("ventas de la categoria blusa", dict(categories=["Blusas"])),
    ("ventas de chaqueta", dict(categories=["Chaquetas"])),
    ("ventas de la sucursal cochabambas", dict(branches=["Ayni Cochabamba"])),
    # rankings dichos de otra forma
    ("rankin de sucursales", dict(group_by=["branch"], metric="revenue")),
    ("ranquin de productos del mes", dict(group_by=["product"], metric="units", period=("this_month", None))),
    ("listado de sucursales por ventas", dict(group_by=["branch"], metric="revenue")),
    ("clasificacion de sucursales", dict(group_by=["branch"], metric="revenue")),
    ("tabla de posiciones de las sucursales", dict(group_by=["branch"], metric="revenue")),
    # abreviaturas en singular tras un número o determinante plural
    ("los 3 prod mas vendidos", dict(group_by=["product"], metric="units", top_n=3)),
    ("el prod mas vendido", dict(group_by=["product"], top_n=1)),
    ("las 2 suc que mas venden", dict(group_by=["branch"], metric="revenue", top_n=2)),
    ("los 5 cli que mas compran", dict(group_by=["customer"], top_n=5)),
    ("vtas x cat del mes", dict(group_by=["category"], period=("this_month", None))),
    # sucursal por palabra distintiva dentro de una frase larga
    ("dime cuanto vendimos ayer en el centro hijita", dict(branches=["Ayni La Paz Centro"])),
    ("oye cuanto se vendio en la zona sur ayer nomas", dict(branches=["Ayni Zona Sur"])),
    ("la plata que entro por la pagina este mes", dict(channel="online", metric="revenue")),
    ("cuanto vendimos en cochabamba pues", dict(branches=["Ayni Cochabamba"])),
])
def test_round_2_entities_rankings_abbreviations(text, expected):
    check(ask(text), expected)


@pytest.mark.parametrize("text", [
    "ventas de la sucursal de santa cruz", "la categoria zapatos", "ventas del producto camisa hawaiana",
    "inventario del producto zapatilla",
])
def test_unknown_entity_named_with_its_type_returns_none(text):
    assert ask(text) is None


@pytest.mark.parametrize("text", [
    "en la sucursal norte, dime las ventas de hoy",  # el contexto descartado nombraba algo que no existe
    "sin las de tarjeta, dime las ventas de hoy",  # ...o una exclusión
    "la categoria zapatos, quiero saber las ventas del mes",
])
def test_ask_pivot_never_drops_a_filter(text):
    assert ask(text) is None


def test_ask_pivot_drops_unrelated_context():
    check(ask("el ano pasado no nos fue bien, pero dime las ventas de este mes"),
          dict(metric="revenue", period=("this_month", None)))


# ---------------------------------------------------------------------------------------------------------
# Ronda de correcciones 3: sin ancla no hay reporte; sinónimos de método de pago
# ---------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("text", [
    # ranking a secas
    "mejor", "algo mejor", "pero mejor", "otra vez pero peor", "el peor", "lo mejor", "top 5", "top diez",
    "el que mas vende", "los que menos venden", "el que menos vende este mes", "ranking", "el mejor", "lo peor",
    # agrupación a secas o referida a un pedido anterior
    "por sucursal", "pero ahora por sucursal", "y ahora por mes", "por dia", "tambien por talla", "ademas por color",
    "y separado por categoria", "ahora desglosado por canal",
    # tiempo a secas o continuaciones
    "ayer", "del mes pasado", "y de la semana pasada", "otra vez", "lo mismo", "eso mismo pero de ayer",
    "y en efectivo", "pero en tienda", "solo online", "cuanto hay en caja",
])
def test_no_anchor_returns_none(text):
    assert ask(text) is None


ANCHORED = [
    ("dime las ventas", dict(metric="revenue")),
    ("y ahora dime cuanto vendimos", dict(metric="revenue")),
    ("pero ahora las ventas por sucursal", dict(group_by=["branch"], metric="revenue")),
    ("otra vez las ventas de ayer", dict(period=("yesterday", None))),
    ("mis mejores clientes", dict(group_by=["customer"])),
    ("el mejor producto del mes", dict(group_by=["product"], top_n=1, period=("this_month", None))),
    ("la peor sucursal", dict(group_by=["branch"], top_n=1, order="asc")),
    ("cual es la sucursal que mas vende", dict(group_by=["branch"], top_n=1)),
    ("los productos que menos se venden", dict(group_by=["product"], order="asc")),
    ("que se vendio mas ayer", dict(group_by=["product"], period=("yesterday", None))),
    ("en que dia vendimos mas", dict(group_by=["day"], top_n=1)),
    ("lo menos vendido por categoria", dict(group_by=["category", "product"], order="asc")),
    ("productos por categoria", dict(group_by=["category"])),
    ("los 3 mejores clientes", dict(group_by=["customer"], top_n=3)),
    ("el mejor dia de ventas", dict(group_by=["day"], top_n=1)),
    ("cuanto entro con tarjeta", dict(payment_methods=["card"], metric="revenue")),
    ("pagos con qr de hoy", dict(payment_methods=["qr"], period=("today", None))),
    ("como nos fue ayer", dict(metric="revenue", period=("yesterday", None))),
    ("x medio de pago de hoy", dict(group_by=["payment_method"], period=("today", None))),
    ("por sucursal de ayer", dict(group_by=["branch"], period=("yesterday", None))),
    # sinónimos de método de pago como agrupación (también con 'x') y su ranking
    ("ventas x medio de pago de hoy", dict(group_by=["payment_method"], metric="revenue", period=("today", None))),
    ("ventas x forma de pago", dict(group_by=["payment_method"])),
    ("ventas por tipo de pago del mes pasado", dict(group_by=["payment_method"], period=("last_month", None))),
    ("ventas segun como pagaron", dict(group_by=["payment_method"])),
    ("pedidos en cada medio de pago", dict(group_by=["payment_method"], metric="orders")),
    ("ingresos separados por medios de pago", dict(group_by=["payment_method"], metric="revenue")),
    ("forma de pago mas usada", dict(group_by=["payment_method"], metric="orders", top_n=1, order="desc")),
    ("el medio de pago menos usado este mes", dict(group_by=["payment_method"], metric="orders", order="asc")),
]


@pytest.mark.parametrize("text, expected", ANCHORED, ids=[t for t, _ in ANCHORED])
def test_anchored_requests_resolve(text, expected):
    check(ask(text), expected)


# Ronda 4: "más/menos vendido(s)" y "lo que más se vende" anclan solos, con producto implícito
IMPLIED_PRODUCT = [
    ("los mas vendidos", dict(group_by=["product"], metric="units", order="desc", top_n=None)),
    ("lo mas vendido de la semana",
     dict(group_by=["product"], metric="units", order="desc", top_n=None, period=("this_week", None))),
    ("lo menos vendido", dict(group_by=["product"], metric="units", order="asc", top_n=None)),
    ("las mas vendidas", dict(group_by=["product"], order="desc", top_n=None)),
    ("los menos vendidos del mes", dict(group_by=["product"], order="asc", period=("this_month", None))),
    ("lo que mas se vende", dict(group_by=["product"], metric="units", order="desc")),
    ("lo que menos se vende en el alto", dict(group_by=["product"], order="asc", branches=["Ayni El Alto"])),
    ("el mas vendido", dict(group_by=["product"], top_n=1, order="desc")),
    ("la menos vendida de octubre", dict(group_by=["product"], top_n=1, order="asc", custom=OCT)),
    ("los 4 mas vendidos de ayer", dict(group_by=["product"], top_n=4, period=("yesterday", None))),
    ("lo que mas se vendio ayer en efectivo", dict(group_by=["product"], payment_methods=["cash"])),
    ("lo mas vendido por sucursal", dict(group_by=["branch", "product"], metric="units")),
    ("que es lo que menos sale", dict(group_by=["product"], order="asc")),
]


@pytest.mark.parametrize("text, expected", IMPLIED_PRODUCT, ids=[t for t, _ in IMPLIED_PRODUCT])
def test_most_sold_construction_implies_product(text, expected):
    q = ask(text)
    check(q, expected)
    assert q.kind == "sales"


# ---------------------------------------------------------------------------------------------------------
# Ola final de correcciones (revisión independiente)
# ---------------------------------------------------------------------------------------------------------
def _names(q):
    return sorted(NAME_BY_ID[i] for i in q.branch_ids + q.product_ids + q.category_ids)


# 1. palabra distintiva suelta: solo sucursales, y nunca pegada a otra palabra desconocida / tras "lo" / "centro de X"
@pytest.mark.parametrize("text, allowed", [
    ("ventas a lo largo del mes", []),
    ("como fueron las ventas a lo largo de octubre", []),
    ("ventas de la zona norte", []),
    ("ventas de la zona este", []),
    ("ventas de la zona central", []),
    ("ventas del centro comercial", []),
    ("dame la informacion basica de ventas de hoy", []),
    ("ventas de zapatos de cuero", []),
    ("ventas del centro de cochabamba", ["Ayni Cochabamba"]),
    ("cuanto vendimos en el centro de el alto", ["Ayni El Alto"]),
    ("ventas de lo alto de la temporada", []),
])
def test_distinctive_word_never_invents_a_filter(text, allowed):
    q = ask(text)
    assert q is None or _names(q) == allowed


@pytest.mark.parametrize("text, names", [
    ("ventas en el centro", ["Ayni La Paz Centro"]), ("ventas del alto de ayer", ["Ayni El Alto"]),
    ("cuanto vendio la sur", ["Ayni Zona Sur"]), ("ventas de la zona sur", ["Ayni Zona Sur"]),
    ("ventas de cochabamba", ["Ayni Cochabamba"]),
    ("ventas de blusa floral", ["Blusa Floral"]), ("ventas de faldas plisadas", ["Falda Plisada"]),
])
def test_branch_partials_and_full_product_names_still_work(text, names):
    assert _names(ask(text)) == names


# 2. la referencia debe ser exactamente el período anterior pegado
@pytest.mark.parametrize("text", [
    "ventas de octubre vs septiembre", "ventas de este mes vs el mes pasado", "ventas de hoy vs ayer",
    "ingresos de este ano comparado con el ano pasado", "pedidos de esta semana contra la semana pasada",
])
def test_adjacent_baseline_compares(text):
    assert ask(text).compare_previous is True


@pytest.mark.parametrize("text", [
    "como nos fue en octubre comparado con agosto", "ventas de hoy vs el lunes",
    "ventas de hoy comparado con el 1 de noviembre", "ventas de octubre vs el 15 de septiembre",
    "ventas de esta semana vs la semana del 19 de octubre", "ventas de este mes vs septiembre",
])
def test_non_adjacent_baseline_returns_none(text):
    assert ask(text) is None


# 3. tipos que no son ventas: solo sucursal/producto; siempre group_by=["product"]
@pytest.mark.parametrize("text", [
    "inventario por talla", "stock critico por categoria", "movimientos diarios", "inventario por sucursal y categoria",
    "existencias por color", "movimientos por semana",
])
def test_non_sales_kinds_reject_other_groupings(text):
    assert ask(text) is None


@pytest.mark.parametrize("text, kind, names", [
    ("inventario de el alto", "inventory", ["Ayni El Alto"]), ("stock por sucursal", "inventory", []),
    ("stock critico en la zona sur", "critical_stock", ["Ayni Zona Sur"]),
    ("movimientos de inventario de la semana pasada", "movements", []),
])
def test_non_sales_kinds_are_clean(text, kind, names):
    q = ask(text)
    assert (q.kind, q.group_by, _names(q)) == (kind, ["product"], names)
    assert (q.metric, q.top_n, q.order, q.channel, q.payment_methods, q.compare_previous) == \
        ("units", None, "desc", "all", [], False)


# 4. pagos que no existen en el sistema
@pytest.mark.parametrize("text", [
    "cuanto cobramos con transferencia bancaria", "ventas a cuenta", "ventas por deposito", "pagos con yape",
    "ventas con tigo money", "ventas pagadas mediante transferencia", "cuanto cobramos de inventario",
])
def test_unsupported_payments_return_none(text):
    assert ask(text) is None


def test_transfers_between_branches_are_still_movements():
    assert ask("transferencias entre sucursales").kind == "movements"


# 5. personas como filtro
@pytest.mark.parametrize("text", [
    "ventas del vendedor juan", "ventas de la cajera ana ayer", "cuanto vendio el vendedor", "ventas de mi vendedor",
    "lo que vendio la cajera hoy",
])
def test_people_as_filters_return_none(text):
    assert ask(text) is None


def test_people_as_requesters_still_resolve():
    check(ask("el contador quiere las ventas de octubre por sucursal"), dict(group_by=["branch"], custom=OCT))


# 6. palabra desconocida justo después de una ranura usada: aviso (o None)
@pytest.mark.parametrize("text", [
    "cuanto vendio miraflores", "ventas sopocachi", "ventas zapatos este mes", "cuanto vendio cocha",
    "cuanto vendio maria", "ventas pronto", "ventas de este mes afectivo",
])
def test_unknown_word_after_a_slot_is_warned(text):
    q, words = interpret_locally_detailed(text, FULL_CATALOG, today=TODAY)
    assert q is None or words


# 7. venta individual, montos y mayoreo: no hay ese reporte
@pytest.mark.parametrize("text", [
    "ventas al por mayor del mes", "ventas por mayor", "ventas al por menor", "la venta mas alta de ayer",
    "el ticket mas alto del mes", "las ventas mas altas del mes", "ventas mayores a 500 bs",
    "ventas de mas de 100 bolivianos", "el pedido mas grande de hoy", "ventas de 200 bs",
])
def test_single_sale_rankings_and_amounts_return_none(text):
    assert ask(text) is None


@pytest.mark.parametrize("text, expected", [
    ("lo mas vendido", dict(group_by=["product"])), ("la peor sucursal", dict(group_by=["branch"], top_n=1)),
    ("ventas en bs del mes", dict(metric="revenue", period=("this_month", None))),
])
def test_single_sale_rules_keep_real_rankings(text, expected):
    check(ask(text), expected)


# 8. períodos
def test_day_uno_de_mes():
    check(ask("ventas del uno de noviembre"), dict(custom=(D(2026, 11, 1), D(2026, 11, 1))))


@pytest.mark.parametrize("text", ["ventas de los lunes", "ventas de todos los lunes", "ventas de cada viernes",
                                  "cuanto vendemos los domingos"])
def test_habitual_weekdays_return_none(text):
    assert ask(text) is None


# 9. demasiadas cláusulas: no se trunca en silencio
def test_too_many_clauses_return_none():
    text = ", ".join(["hola"] * 12 + ["ventas de hoy"])
    assert interpret_locally_detailed(text, FULL_CATALOG, today=TODAY) == (None, [])


# 10. corrector: la primera letra no se cambia en palabras que cambian el reporte
@pytest.mark.parametrize("word", ["renta", "afectivo", "lentas", "rentas", "tentas", "pedidas"])
def test_fuzzy_never_changes_the_first_letter_of_high_impact_words(word):
    assert corrector_for(frozenset()).correct(word) in (None, word) or \
        corrector_for(frozenset()).correct(word)[0] == word[0]


# 12. caracteres de compatibilidad
def test_fullwidth_text_is_folded():
    check(ask("ｖｅｎｔａｓ de hoy"), dict(metric="revenue", period=("today", None)))


# Últimos ajustes: "vs/con" entre cosas que no son períodos agrupa, no compara con el período anterior
@pytest.mark.parametrize("text, group", [
    ("comparame online vs tienda de este mes", "channel"), ("online con tienda fisica este mes", "channel"),
    ("efectivo vs tarjeta este mes", "payment_method"), ("compara efectivo con tarjeta este mes", "payment_method"),
    ("ayni zona sur vs ayni el alto este mes", "branch"), ("compara la sur con el alto este mes", "branch"),
    ("compara las sucursales este mes", "branch"),
])
def test_entity_comparison_groups_without_previous_period(text, group):
    q = ask(text)
    assert (q.group_by, q.compare_previous, q.period.preset) == ([group], False, "this_month")


@pytest.mark.parametrize("text, preset", [
    ("ventas de este mes vs el mes pasado", "this_month"), ("ventas de hoy vs ayer", "today"),
    ("comparame las ventas de este mes con el anterior", "this_month"),
    ("ventas de este mes comparado con el mes anterior", "this_month"),
    ("ventas de octubre vs septiembre", "custom"),
])
def test_period_comparison_still_compares(text, preset):
    q = ask(text)
    assert (q.compare_previous, q.period.preset) == (True, preset)


# "la tienda / el local / la sede de <nombre>" nombra una sucursal; si no existe -> None
@pytest.mark.parametrize("text", [
    "ventas de la tienda de santa cruz", "ventas del local de sopocachi", "ventas de la sede de potosi",
    "cuanto vendio la tienda de la calle comercio", "el local de sopocachi",
])
def test_store_word_naming_an_unknown_branch_returns_none(text):
    assert ask(text) is None


@pytest.mark.parametrize("text, expected", [
    ("ventas de la tienda del alto", dict(branches=["Ayni El Alto"], channel="all")),
    ("ventas en tienda fisica de ayer", dict(channel="store", period=("yesterday", None))),
    ("pedidos en tienda de hoy", dict(channel="store", metric="orders")),
    ("ventas en caja de hoy", dict(channel="store")),
    # "tienda" sin "de/del <nombre>" es el canal tienda
    ("ventas de la tienda", dict(channel="store", branches=[])),
    ("cuanto vendimos en la tienda ayer", dict(channel="store", period=("yesterday", None))),
    ("ventas en la tienda este mes", dict(channel="store", period=("this_month", None))),
    ("lo de la tienda", dict(channel="store", metric="revenue")),
    ("ventas de la tienda de ayer", dict(channel="store", period=("yesterday", None))),
    # con un nombre del catálogo es la sucursal, no el canal
    ("ventas de la tienda sur", dict(branches=["Ayni Zona Sur"], channel="all")),
    ("online vs tienda", dict(group_by=["channel"], channel="all")),
])
def test_store_channel_only_with_its_qualifiers(text, expected):
    check(ask(text), expected)



@pytest.mark.parametrize("text", ["la tienda", "cuanto hay en caja", "abre la caja"])
def test_store_word_alone_is_not_a_request(text):
    assert ask(text) is None
