"""Vocabulario del intérprete de reportes (texto ya normalizado: minúsculas, sin tildes, números en cifras).

CÓMO AGREGAR UN SINÓNIMO
- Cada patrón es una expresión regular sobre palabras completas separadas por un espacio (sin tildes).
- Sinónimo de algo que ya existe: agrégalo a la alternativa correspondiente, p. ej. un nuevo nombre para el canal
  en línea va en CHANNEL_ONLINE; una nueva forma de decir "ingresos" va en METRIC_STRONG["revenue"].
- Palabra que el usuario puede decir pero que NO sabemos resolver (p. ej. "semestre", "comisión"): agrégala a FLAG.
  Si aparece sin haber sido usada por ningún patrón, la frase devuelve None (regla de oro: nunca ignorar algo que
  reconocemos pero no sabemos resolver).
- Palabra de relleno que no cambia el sentido ("reporte", "porfa"): agrégala a STOP.
- Cualquier otra palabra es "desconocida": se tolera si la frase tiene un pedido de reporte reconocible
  (nombres de productos de otra empresa, ruido del dictado), pero sola no forma un reporte.
- Después de cambiar algo, correr tests/test_report_interpreter.py y tests/test_report_interpreter_corpus.py.
"""
import re


def rx(pattern: str) -> re.Pattern:
    """Compila un patrón que solo coincide con palabras completas."""
    return re.compile(rf"(?<![^ ])(?:{pattern})(?![^ ])")


MONTHS = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
    "septiembre": 9, "setiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
}
WEEKDAYS = {"lunes": 0, "martes": 1, "miercoles": 2, "jueves": 3, "viernes": 4, "sabado": 5, "domingo": 6}
MONTH = "|".join(MONTHS)
WEEKDAY = "|".join(WEEKDAYS)

# --- números en palabras -----------------------------------------------------------------------------
NUM_UNITS = {"un": 1, "uno": 1, "una": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6, "siete": 7,
             "ocho": 8, "nueve": 9}
NUM_TENS = {"treinta": 30, "cuarenta": 40, "cincuenta": 50, "sesenta": 60, "setenta": 70, "ochenta": 80,
            "noventa": 90}
NUM_WORDS = {
    **NUM_UNITS, **NUM_TENS,
    "diez": 10, "once": 11, "doce": 12, "trece": 13, "catorce": 14, "quince": 15, "dieciseis": 16,
    "diecisiete": 17, "dieciocho": 18, "diecinueve": 19, "veinte": 20, "veintiun": 21,
    **{"veinti" + w: 20 + n for w, n in NUM_UNITS.items() if w != "un"},
    "cien": 100, "ciento": 100, "doscientos": 200, "trescientos": 300, "cuatrocientos": 400, "quinientos": 500,
    "seiscientos": 600, "setecientos": 700, "ochocientos": 800, "novecientos": 900, "mil": 1000,
}
# "un/una/uno" solo es número delante de una unidad de tiempo o después de "top" ("dame un reporte" no lleva número)
UNIT_AFTER_ONE = {"dia", "semana", "mes", "ano", "trimestre", "semestre"}

# --- frases de relleno que contienen palabras con significado ("buenos dias", "por favor") ----------------
FILLER = rx(r"buen[oa]s (?:dias|tardes|noches)|por favor|porfa(?:vor)?|si eres tan amable|por medio de la presente|"
           r"a traves de la presente|de antemano|sin otro particular")

# --- dimensiones ---------------------------------------------------------------------------------------
DIM_WORDS = {
    "payment_method": r"(?:metodos?|formas?|medios?|tipos?|maneras?|modos?) de pago|metodos?|"
                      r"como (?:nos )?(?:pagaron|pagan|pago|pagaban)",
    "product": r"productos?|prendas?|articulos?|items?|modelos?|referencias?",
    "variant": r"variantes?",
    "category": r"categorias?|rubros?|lineas?",
    "branch": r"sucursal(?:es)?|tiendas?|locales?|agencias?",
    "size": r"tallas?",
    "color": r"colou?r(?:es)?",
    "channel": r"canal(?:es)?",
    "customer": r"clientes?|compradores?",
    "day": r"dias?",
    "week": r"semanas?",
    "month": r"mes(?:es)?",
}
DIM_ANY = "|".join(f"(?:{p})" for p in DIM_WORDS.values())
DIM_PLURAL = (r"(?:metodos|formas|medios|tipos|maneras|modos) de pago|productos|prendas|articulos|items|modelos|variantes|categorias|"
              r"rubros|lineas|sucursales|tiendas|locales|agencias|tallas|colou?res|canales|clientes|compradores|"
              r"dias|semanas|meses")
DIM_TIME_ADJ = [
    (rx(r"diari[oa]s?|diariamente|dia a dia|dia por dia"), "day"),
    (rx(r"semanal(?:es)?|semanalmente|semana a semana|semana por semana"), "week"),
    (rx(r"mensual(?:es)?|mensualmente|mes a mes|mes por mes"), "month"),
]
# "por X", "de cada X", "desglosado por X"... (la X es una dimensión)
GROUP_CUE = rx(
    r"(?:(?:agrupad|desglosad|separad|dividid|segmentad|organizad|clasificad|ordenad|distribuid|repartid|"
    r"abiert|detallad)[oa]s? )?(?:por cada|de cada|en cada|para cada|cada|por|segun|desglose de)"
    rf"(?: (?:el|la|los|las|su|sus|tipo de))? (?P<d>{DIM_ANY})"
)
GROUP_CHAIN = re.compile(rf" (?:y|e)(?: (?:por cada|de cada|en cada|cada|por|segun))?(?: (?:el|la|los|las))? "
                         rf"(?P<d>{DIM_ANY})(?![^ ])")
# "comparame las sucursales", "entre las sucursales": agrupar, no comparar períodos
GROUP_COMPARE = rx(
    rf"(?:compar\w*|comparativ[oa]|comparacion)(?: (?:de|entre))?(?: (?:las|los|mis|nuestras|nuestros))? "
    rf"(?P<d>{DIM_PLURAL})|entre (?:las |los )?(?:distint[oa]s |diferentes |tod[oa]s l[oa]s )?(?P<e>{DIM_PLURAL})"
)
# sustantivo que nombra a la entidad del catálogo que lo sigue: "la sucursal (de) Ayni Zona Sur" -> filtro
HEAD_NOUNS = [
    (rx(r"(?:sucursal(?:es)?|tiendas?|locales?|agencias?)(?: (?:de|del|la|el|en))*(?= _b)"), "branch"),
    (rx(r"(?:categorias?|lineas?|rubros?)(?: (?:de|del|la|el|los|las))*(?= _c)"), "category"),
    (rx(r"(?:productos?|prendas?|articulos?|modelos?)(?: (?:de|del|la|el))*(?= _p)"), "product"),
]
CANDIDATE = rx(rf"quien(?:es)?|{DIM_ANY}")
PRODUCT_NOUN = re.compile(DIM_WORDS["product"])
INTENSIFIERS = {"mas", "menos", "muy", "tan", "mayor", "menor"}  # "el más alto" no es la sucursal El Alto

# --- tipo de reporte -----------------------------------------------------------------------------------
KINDS = [
    ("critical_stock", rx(
        r"stock (?:critico|minimo|bajo)|(?:poco|bajo|sin|cero|escaso|minimo) stock|sin existencias|"
        r"existencias bajas|(?:por|a punto de) agotar\w*|agotad[oa]s?|se (?:esta|estan) (?:acabando|terminando)|"
        r"(?:esta|estan) por acabar\w*|(?:que )?(?:falta|faltan|hay que|toca|necesito|debo) reponer|por reponer|"
        r"necesita(?:n)? reposicion")),
    ("movements", rx(
        r"movimientos?(?: de (?:inventario|stock|mercaderia|mercancia|almacen))?|entradas y salidas|"
        r"(?:entradas|salidas|ingresos?) de (?:mercaderia|mercancia|stock|inventario|productos)|"
        r"lleg\w* (?:la |el )?(?:mercaderia|mercancia|pedido del proveedor)|mercaderia que lleg\w*|"
        r"transferencias?|traspasos?|reposicion(?:es)?|reabastecimientos?|ajustes? de (?:inventario|stock)")),
    ("inventory", rx(
        r"inventario|existencias?|mercaderia|mercancia|que (?:tengo|tenemos|hay) de|"
        r"stock(?: (?:actual|disponible))?|(?:nos )?(?:queda|quedan)(?: en stock)?|"
        r"disponibles? en (?:stock|tienda|almacen)|hay en (?:stock|almacen|bodega)|tenemos en (?:stock|almacen|bodega)")),
]

# --- canal y método de pago ----------------------------------------------------------------------------
_ONLINE = (r"online|en linea|internet|web|pagina(?: web)?|app|aplicacion|tienda (?:online|virtual|en linea|web)|"
           r"e commerce|ecommerce|virtual(?:es)?")
_STORE = (r"tiendas? fisicas?|tienda|locale?s? fisicos?|caja|mostrador|punto de venta|presencial(?:es|mente)?|"
          r"en persona")
CHANNEL_VS = rx(rf"(?:{_ONLINE}) (?:vs|versus|contra|o|y|con|frente a|comparado con) (?:en |la |las |el )*(?:{_STORE})|"
                rf"(?:{_STORE}) (?:vs|versus|contra|o|y|con|frente a|comparado con) (?:en |la |las |el |por )*"
                rf"(?:{_ONLINE})")
CHANNEL_ONLINE = rx(rf"(?:(?:por|en|via|desde|de) (?:la |el )?)?(?:{_ONLINE})")
# "tienda" (con o sin artículo) es el canal salvo que siga "de/del <nombre>" (eso nombra una sucursal: aclaración 32)
CHANNEL_STORE = rx(r"(?:(?:en|de|por|desde) (?:la |el |las |los )?)(?:tiendas? fisicas?|tienda(?! (?:de|del) (?:el |la |los |las )?[a-z])|"
                   r"locale?s? fisicos?|caja|mostrador|punto de venta)|tiendas? fisicas?|presencial(?:es|mente)?|"
                   r"en persona|mostrador")
_PAY_PREFIX = (r"(?:(?:se )?(?:pagad[oa]s?|pagaron|pagos?|cobrad[oa]s?|cobros?|abonad[oa]s?|cancelad[oa]s?) )?"
               r"(?:(?:con|en|al|por|mediante|via) )?(?:la |el |una )?")
PAYMENTS = [
    ("cash", rx(_PAY_PREFIX + r"(?:efectivo|contado|cash)")),
    ("card", rx(_PAY_PREFIX + r"(?:tarjetas?(?: de (?:credito|debito))?|stripe)")),
    ("qr", rx(_PAY_PREFIX + r"(?:(?:codigo |cobro )?qr)")),
    ("wallet", rx(_PAY_PREFIX + r"(?:billeteras?(?: (?:digital|virtual|movil|electronica)(?:es)?)?|monedero)")),
]

_PM = r"efectivo|contado|tarjetas?|stripe|(?:codigo )?qr|billeteras?"
PAYMENT_VS = rx(rf"(?:(?:pagos?|cobros?) )?(?:en |con |al |por )?(?:{_PM}) (?:vs|versus|contra|frente a|comparado con|con)"
                rf"(?: (?:en|con|al|por|la|el))* (?:{_PM})(?=(?: (?:vs|versus|contra))?)")

# --- comparación con el período anterior ----------------------------------------------------------------
COMPARE = rx(
    r"(?:comparad[oa]s?|comparando(?:lo|la|los|las)?|en comparacion|comparacion|comparativ[oa]|compar[ae]r?|"
    r"comparame|comparalo|vs|versus|contra|frente|respecto|en relacion)(?: (?:a|al|con|de|del))?"
    r"(?: (?:el|la|lo|los|las))?(?: (?:periodo|mes|ano|semana|trimestre|dia|gestion))?(?: (?:anterior|previo|pasad[oa]))?"
)

COMPARE_TARGET = rx(r"(?:con|a|al|y|contra)(?: (?:el|la|lo))?(?: (?:periodo|mes|ano|semana|trimestre|dia|gestion))? "
                    r"(?:anterior|previo)")  # "comparame las ventas con el periodo anterior"

# --- métricas -------------------------------------------------------------------------------------------
METRIC_STRONG = [  # el orden importa: la primera consume sus palabras ("ticket promedio" no es "tickets")
    ("avg_ticket", rx(
        r"tickets? (?:promedio|medio)|(?:valor|monto|importe|gasto|compra|venta|consumo|pago) (?:promedio|medio)|"
        r"promedio (?:por|de|del) (?:venta|compra|ticket|pedido|transaccion|orden|boleta)|promedio de (?:gasto|compra)|"
        r"(?:gast\w*|compr\w*|pag\w*) (?:en )?promedio")),  # "cuánto gastó en promedio cada cliente"
    ("customers", rx(
        r"(?:cuant[oa]s|cantidad de|numero de|total de|nro de|conteo de) (?:los )?(?:clientes|compradores)"
        r"(?: (?:distintos|unicos|diferentes))?|(?:clientes|compradores) (?:distintos|unicos|diferentes)")),
    ("orders", rx(
        r"(?:cantidad|numero|total|nro) de (?:pedidos|ordenes|transacciones|tickets|boletas)|"
        r"pedidos?|ordenes|ordenes de compra|transacciones?|tickets?|boletas?|facturas|operaciones|"
        r"(?:cuant[oa]s|numero de|cantidad de|nro de) (?:ventas|compras)|cuantas veces (?:se )?vend\w*")),
    ("units", rx(r"unidades|cantidad(?: vendida)?|piezas|volumen(?: de ventas)?")),
    ("revenue", rx(
        r"ingresos?|facturacion|factur(?:a|amos|ado|ada|o|aron|e|an|aba)|plata|dinero|recaud\w*|montos?(?: total)?|"
        r"importe|total vendido|lo vendido|ventas totales|total de ventas|recaudacion")),
]
# preguntas de estado: "como nos fue", "como van las ventas", "que tal las ventas"
STATUS = rx(r"(?:que tan|cuan) bien (?:nos fue|nos va|vamos|estamos|vendimos|nos ha ido|anduvimos)|"
            r"como estamos de ventas|(?:los )?numeros|balance(?: de ventas)?|como cerramos|"
            r"como (?:nos|me|le) (?:fue|va|ha ido|esta yendo)|como (?:vamos|van|estamos|estuvo|estuvieron|anduvo|"
            r"andamos|andan)|que tal (?:nos fue|vamos|van|estuvo|estuvieron|fue)")
VEND = r"vend(?:e|en|o|i|io|ia|ian|imos|ieron|ido|ida|er|emos|amos|iendo)"
# familia de verbos que en contexto de prendas significan "se vendió" (cantidad): salir, moverse, rotar, despachar,
# irse, llevarse. Para agregar uno: sumar sus formas a MOVED (una sola palabra) o a MOVED_PHRASE (con "se").
MOVED = (r"sal(?:io|ieron|e|en|ido|ian|ia)|movi(?:o|eron|do|dos|das)|mueven?|rot(?:o|aron|a|an|ado|ados|adas)|"
         r"despach(?:o|aron|amos|a|an|ado|ados|adas|e)")
MOVED_PHRASE = r"se (?:fue|fueron|va|van|iban|han ido|llev(?:o|aron|a|an|aban|ado))|(?:se )?(?:" + MOVED + ")"
WEAK_UNITS = rx(rf"vendid[oa]s|{MOVED_PHRASE}|cuant[oa]s(?= (?:\S+ ){{0,4}}?(?:{VEND}|{MOVED}|se vendieron|"
                rf"se (?:fue|fueron|van|llev\w+))(?![^ ]))|rotacion")
SPEND = r"gast(?:o|a|an|aron|ado|aba|aban)"  # "el cliente que más gastó" (los "gastos" del negocio no: FLAG)
WEAK_REVENUE = rx(rf"ventas?|{VEND}|{SPEND}|compr(?:a|an|o|aron|amos|ado|ada|as)|cuanto (?:llevamos|vamos)")

# --- rankings --------------------------------------------------------------------------------------------
_RANKABLE = DIM_PLURAL.replace("|dias|semanas|meses", "")  # "15 dias" es un período, no un top
TOP_N = rx(rf"top (?P<a>\d+)|(?P<b>\d+)(?= (?:mejores |peores |principales |primer[oa]s )?(?:{_RANKABLE})(?![^ ]))|"
           r"(?:los|las) (?P<c>\d+)(?= (?:mas|menos|mejores|peores|principales)(?![^ ]))|primer[oa]s (?P<d>\d+)|(?P<e>\d+) primer[oa]s")
# palabras que hacen de "mas/menos" un ranking cuando están al lado ("vende mas", "mas vendido", "con menos ventas")
SALES_NEAR = re.compile(rf"{VEND}|{SPEND}|{MOVED}|vendid[oa]s?|pedid[oa]s?|alt[oa]s?|baj[oa]s?|elevad[oa]s?|compr\w*|"
                        r"factur\w*|recaud\w*|ingres\w*|ventas?|ordenes|unidades|plata|"
                        r"dinero|usad[oa]s?|usan?|usaron|utiliza\w*|prefer\w*|prefier\w*|popular(?:es)?|movid[oa]s?|salid[oa]s?|salieron|sale|salen|"
                        r"gener\w*|transacciones|tickets?|clientes|piden|pidieron|rotacion")
SOLD = re.compile(rf"vendid[oa]s?|{MOVED}|rotacion")
USED = re.compile(r"usad[oa]s?|usan?|usaron|utiliza\w*|popular(?:es)?|prefer\w*|prefier\w*")
LOW = re.compile(r"baj[oa]s?")  # "el ticket más bajo" = el menor
RANK_SKIP = {"se", "nos", "lo", "le", "les", "me", "que", "la", "el", "los", "las", "han", "ha", "hemos", "fue",
             "fueron", "es", "son", "hubo", "tuvo", "tuvieron", "con", "de", "del"}
ARTICLES = {"el", "la", "los", "las", "un", "una", "su", "sus", "tipo", "de"}
RANK_DESC = {"mejor", "mejores", "mayor", "mayores", "estrella", "lider", "lideres", "principal", "principales"}
# rankings dichos como lista o como suena "ranking" ("rankin", "ranquin"); "listado/tabla de <dimensión>" también
RANK_LIST = {"top", "ranking", "rankings", "rankin", "ranquin", "ranquing", "ranquines", "clasificacion",
             "posiciones"}
RANK_ASC = {"peor", "peores", "menor", "menores"}

# --- clasificación de lo que sobra -------------------------------------------------------------------------
STOP = set("""
de del la el los las lo un una unos unas y e o u a al en con por para sobre entre que como cual cuales cuanto
cuanta cuantos cuantas donde cuando es son fue fueron era ser sea sido ha han hemos he hay hubo tuvimos tenemos tiene
tienen tuvo tengo esta estan estuvo estuvieron estamos va van vamos se me te nos le les mi mis tu tus su sus nuestro
nuestra nuestros nuestras este estos estas ese esa eso esos esas reporte reportes informe informes resumen datos dato
listado lista grafico grafica tabla estadisticas estadistica analisis detalle detallado desglose total totales numero
cifras cifra informacion info consulta quiero queria quisiera necesito necesitaria necesitamos saber ver verlo verla
verlos mostrar mostrarme muestrame muestra mostra muestreme dame damelo dime decir decirme sacame saca genera generame
generar hazme haga puedes podrias puede podria oye oiga eh em mm ah bueno ok okay vale gracias hola che pues entonces
ahora actual actuales general todo todos todas toda hicimos entro entraron llevamos hecho tal emitidos emitidas
registrados registradas realizados realizadas hechos hechas favor me muestres muestre quisieras ensename ensenar
traeme trae dar darme ver consultar revisar revisa revisame calcula calculame cuentame dimelo listar lista lista
hubieron habido sacar tambien solo solamente nomas ya aqui alli asi durante mediante hacia tras pero porque si
quisiera quisieramos gustaria podrias podria podrian puede podes pudieras saber sepa ayudarme ayudame ayuda
mostrame contame decime pasame mandame tirame armame preparame prepara prepares hacerme haceme decis
creo crees parece sabes sabe onda rapido rapidito urgente jefe jefa senor senora don dona amigo amiga querido
querida hija hijo mama papa disculpa disculpe perdon permiso luego tu usted ustedes vos yo
nosotros ellos esto aquello algo cosa cosas tema temas pregunta preguntar consulto consultar acerca respecto
dato dime gracias muchas porfis plis please ok listo bueno entonces igual tipo ver
mostrarnos decirnos darnos traer traerme verificar chequear checar revisar mirar mira
solicito solicitamos solicitar estimado estimada estimados sistema atentamente saludos cordiales agradezco
bs bolivianos
digame dimelo muestreme oye mira fijate ayudame vea veamos haber nuestro nuestra exactamente aproximadamente
""".split())
FLAG = re.compile(
    # tiempo que no sabemos resolver
    r"dias?|semanas?|mes(?:es)?|anos?|trimestres?|semestres?|bimestres?|quincenas?|hoy|ayer|anoche|manana|tarde|"
    r"tardes|noche|noches|madrugada|horas?|fechas?|hace|antes|despues|desde|hasta|proxim[oa]s?|siguientes?|"
    r"pasad[oa]s?|anterior(?:es)?|previ[oa]s?|ultim[oa]s?|primer[oa]?s?|navidad|feriados?|fin|finde|temporadas?|"
    r"verano|invierno|otono|primavera|carnavales?|vacaciones|gestion|siempre|nunca|mism[oa]s?|aniversario|inicio|"
    r"comienzo|principios?|mediados|finales?|epoca|periodo|periodos|reciente|recientes|ultimamente|viene|vienen|paso|"
    r"entrante|venidero|aguinaldo|black|friday|cyber|ciber|madres?|padres?|valentin|pascuas?|halloween|fiestas?|"
    r"ferias?|festividad\w*|rebajas?|liquidacion|"
    rf"{MONTH}|{WEEKDAY}|lunes|sabados|domingos|"
    # métricas sin datos o no soportadas
    r"ganancias?|utilidad(?:es)?|margen(?:es)?|costos?|coste|gastos?|rentabilidad|beneficios?|deudas?|deben|debe|"
    r"adeud\w*|cobrar|fiado|credito|debito|impuestos?|iva|comision(?:es)?|descuentos?|devoluciones|devolucion|"
    r"reembolsos?|perdidas?|merma|presupuestos?|metas?|objetivos?|proyeccion|pronostico|prediccion|estimad\w*|"
    r"net[oa]s?|sueldos?|salarios?|pagamos|pague|gastamos|gastos|luz|alquiler|nuevos?|recurrentes|frecuentes?|bien|mal|malo|regular|"
    r"promedio|media|porcentajes?|crecimiento|tendencias?|variacion|proporcion|ganamos|gane|gano|"
    r"sub(?:e|en|io|ieron|ido)|baj(?:aron|an|ado)|crec(?:e|en|io|ieron|ido)|aument\w*|disminu\w*|ca(?:yo|yeron|e|en)|"
    r"mejor(?:o|aron|ado)|empeor\w*|"
    # negaciones y exclusiones: "ventas sin tarjeta" no puede volverse "ventas con tarjeta"
    r"no|sin|excepto|salvo|excluyendo|exclusivo|fuera|ningun[oa]?|nada|"
    # acciones (el intérprete solo consulta) y estados de pedido que el reporte no distingue
    r"borr\w*|elimin\w*|cancel\w*|anul\w*|modific\w*|cambi\w*|edit\w*|agreg\w*|envia\w*|envie|pq|mediodia|"
    r"egresos?|cierres?|arqueos?|apertura|saldos?|turnos?|dolares|usd|euros?|"
    r"pendientes?|entregad[oa]s?|despachad[oa]s?|enviad[oa]s?|rechazad[oa]s?|reservad[oa]s?|apartad[oa]s?|"
    # canal, pago, ranking y comparación sin resolver
    r"tiendas?|online|web|internet|pagina|app|caja|presencial\w*|mostrador|fisic[oa]s?|virtual(?:es)?|efectivo|"
    r"contado|tarjetas?|qr|billeteras?|stripe|pagos?|pagad[oa]s?|pagaron|cobros?|cobrad[oa]s?|cheques?|"
    r"depositos?|delivery|domicilio|envios?|mas|menos|mejor(?:es)?|peor(?:es)?|mayor(?:es)?|menor(?:es)?|top|"
    r"compar\w*|vs|versus|contra|frente|ranking|rankin|ranquin|ranquing|clasificacion|posiciones|"
    # tipos de reporte y entidades sin resolver
    r"stock|inventario|existencias?|movimientos?|clientes?|compradores?|quien(?:es)?|unidades|cantidad|pedidos?|"
    r"ventas?|ingresos?|marcas?|temporadas?|"
    rf"{DIM_ANY}"
)


# --- abreviaturas de teléfono (se expanden antes de todo; clarificación 22) ---------------------------------
ABBREVIATIONS = {
    "vtas": "ventas", "vts": "ventas", "sucs": "sucursales", "x": "por", "prods": "productos", "clis": "clientes",
    "arts": "articulos", "q": "que", "xfa": "por favor", "xfavor": "por favor",
    "porfa": "por favor", "tmb": "tambien", "tb": "tambien", "tbn": "tambien", "pa": "para", "d": "de",
    "cant": "cantidad", "cats": "categorias", "invent": "inventario", "inv": "inventario",
    "hs": "horas", "hrs": "horas",
}

# --- vocabulario para corregir errores de tipeo o del dictado (solo palabras reales, flexionadas) -------------
FUZZY_VOCAB = set("""
ventas venta vendimos vendido vendidos vendida vendidas vendio vendieron vende venden vender vendemos vendi
ingresos ingreso facturacion facturamos facturado factura facturo dinero plata recaudado recaudamos recaudacion
monto importe pedidos pedido ordenes transacciones tickets ticket promedio unidades cantidad prendas prenda
productos producto piezas articulos sucursal sucursales tienda tiendas categoria categorias clientes cliente
compran compraron compras compra variante variantes tallas talla colores color canal canales metodo pago pagos
efectivo contado tarjeta tarjetas billetera internet online presencial presenciales fisica mostrador
inventario existencias stock critico criticos agotados agotadas agotarse acabando reponer movimientos
transferencias reposiciones mercaderia entradas salidas hoy ayer anoche semana semanas pasada pasado anterior
ultimos ultimas ultimo ultima trimestre mensual mensuales semanal semanales diario diaria diarias diarios
semestre quincena meses mes este esta lunes martes miercoles jueves viernes sabado domingo enero febrero
marzo abril mayo junio julio agosto septiembre setiembre octubre noviembre diciembre mejores mejor peores peor
menos mayor menor comparado compara comparame comparar comparacion versus contra cuanto cuanta cuantos cuantas
cuales quien quienes dias semana reporte informe resumen muestrame mostrame dame quisiera necesito gracias
favor ganancia ganancias utilidad margen costo costos salieron salio despacharon rotacion movio
cuatro cinco quince veinte treinta cuarenta cincuenta sesenta setenta ochenta noventa
""".split())

# dos métricas distintas unidas por "y" = varios reportes a la vez -> None (clarificación 20)
METRIC_WORDS = {
    "revenue": r"ventas?|ingresos?|facturacion|plata|dinero|recaudacion|monto|vend(?:imos|io|i|ieron)",
    "orders": r"pedidos?|ordenes|transacciones|tickets?",
    "units": r"unidades|prendas|piezas",
    "avg_ticket": r"promedio",
    "customers": r"clientes",
}
METRIC_PAIR = rx(r"(?P<first>" + "|".join(METRIC_WORDS.values()) + r")(?: \S+){0,1} (?:y|e) "
                 r"(?:(?:el|la|los|las|cuant[oa]s?|tambien|ademas) )*(?P<second>" + "|".join(METRIC_WORDS.values()) + ")")

# palabras que cambian el reporte (pago, canal, tipo, métrica): solo se corrigen con cambios de letra o transposición
FUZZY_HIGH_IMPACT = set("""
efectivo contado tarjeta tarjetas billetera internet online presencial presenciales fisica mostrador tienda
inventario existencias stock critico agotados agotadas movimientos transferencias reposiciones mercaderia
ventas venta ingresos ingreso facturacion dinero plata pedidos pedido ordenes transacciones tickets ticket
promedio unidades cantidad clientes cliente
""".split())

# abreviaturas que toman singular o plural según lo que va antes ("los 3 prod" -> productos, "el prod" -> producto)
ABBREVIATIONS_NUMBER = {
    "prod": ("producto", "productos"), "suc": ("sucursal", "sucursales"), "cat": ("categoria", "categorias"),
    "cli": ("cliente", "clientes"), "vta": ("venta", "ventas"), "art": ("articulo", "articulos"),
}
PLURAL_DETERMINERS = {"los", "las", "unos", "unas", "mis", "sus", "nuestros", "nuestras", "todos", "todas", "varios",
                      "varias", "cuantos", "cuantas", "algunos", "algunas", "dos", "tres", "cinco", "diez"}

# cláusulas: conectores de digresión (se quitan) y frases que introducen el pedido (se corta antes)
CLAUSE_SPLIT = re.compile(
    r" (pero ahora|pero|porque|aunque|ya que|y ahora|asi que|ahora bien|o sea|nada mas eso|nomas eso|eso nomas) |"
    r" (?=(?:digame|dime|decime|quiero saber|quisiera saber|necesito saber|quiero ver|quisiera ver|"
    r"me podrias decir|me puede decir|me puedes decir|podrias decirme|lo que quiero (?:saber|ver) es|"
    r"mi pregunta es|la consulta es) )")
ASIDE_CONNECTORS = {"porque", "aunque", "ya que"}  # lo que sigue explica, no pide
PIVOT_CONNECTORS = {"pero", "pero ahora", "y ahora", "ahora bien", "ask"}  # "ask": "dígame", "quiero saber"...  # lo que sigue puede reemplazar lo anterior

PLACE_ARTICLES = {"el", "la", "los", "las", "de", "del", "en", "al"}  # "en el centro": nombre de lugar tras artículo

# personas que se mencionan al pedir ("el contador quiere…"): no cambian el reporte, pero no existe agrupar ni
# rankear por ellas ("ventas por vendedor", "el mejor cajero" -> None)
ROLE = re.compile(r"vendedor(?:es|as?)?|cajer[oa]s?|emplead[oa]s?|contador(?:es|as?)?|gerentes?|encargad[oa]s?|"
                  r"duen[oa]s?|soci[oa]s?|proveedor(?:es|as?)?|administrador(?:es|as?)?|jef[ae]s?|"
                  r"trabajador(?:es|as?)?|personal|nieto|nieta|hij[oa]s?|hijit[oa]|joven|senorita")
FILTER_WORDS = re.compile(rf"{DIM_WORDS['branch']}|{DIM_WORDS['product']}|{DIM_WORDS['category']}|"
                          r"sin|excepto|salvo|excluyendo|solo|solamente|unicamente")

# anclas de un pedido (ver _anchored): sustantivos de ventas/dinero y verbos de dinero
SALES_NOUN = re.compile(r"ventas?|ingresos?|facturacion|plata|dinero|recaudacion|montos?|importe|pedidos?|ordenes|"
                        r"transacciones|tickets?|unidades|cantidad|piezas")
MONEY_VERB = re.compile(r"entr(?:o|aron)|cobr\w+|pag(?:os|aron|ado|ados|ada|adas)|recaud\w+|factur\w+")
QUESTION_WORDS = {"que", "cual", "cuales", "quien", "quienes"}
BEFORE_QUESTION = {"en", "de", "con", "a", "por", "para", "y", "dime", "digame", "decime", "saber", "ver", "sabes",
                   "pregunto", "_f"}

# --- lo que el sistema no soporta y se reconoce como tal (-> None) ----------------------------------------------
# pagos que no existen (transferencia, depósito, a cuenta, billeteras de terceros), mayoreo, días habituales
UNSUPPORTED = rx(
    r"(?:con|por|via|mediante|en) (?:una |la |las )?transferencias?(?: bancarias?)?|transferencias? bancarias?|"
    r"depositos?|a cuenta|tigo money|yape|(?:al )?por (?:mayor|menor)|al mayoreo|"
    rf"(?:los|todos los|cada) (?:{WEEKDAY}|sabados|domingos)"
)
MOVED_RE = re.compile(MOVED)
PERSON_DETERMINERS = {"mi", "mis", "nuestro", "nuestra", "el", "la", "los", "las", "su", "sus", "un", "una"}
# después de una ranura, estas palabras no son contenido ("ventas poco claras" no; "vendimos mucho" sí es relleno)
HARMLESS_AFTER_SLOT = {"poco", "mucho", "muchas", "muchos", "bien", "ya", "nomas", "pues", "todavia", "aun",
                       "tambien", "nada", "exactamente", "aproximadamente", "total", "general", "completo",
                       "completa", "entero", "entera", "porfa", "rapido", "hijita", "hijito", "senor", "senora"}
# "la tienda / sucursal / el local / la sede de <nombre>": nombra una sucursal (aclaración 10 y 32)
BRANCH_NOUNS = re.compile(r"tiendas?|sucursal(?:es)?|locale?s?|sedes?|agencias?")
