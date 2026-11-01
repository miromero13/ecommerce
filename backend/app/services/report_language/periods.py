"""Expresiones de tiempo -> PeriodSpec, relativas a `today` (inyectable para que las pruebas sean deterministas)."""
from datetime import date, timedelta

from app.schemas.analytics_schema import PeriodSpec
from app.services.report_language.lexicon import MONTH, MONTHS, WEEKDAY, WEEKDAYS, rx

MAX_DAYS = 3650  # rango explícito más largo que se acepta (10 años)


class InvalidPeriod(ValueError):
    """Se reconoció una fecha pero no existe (31/02) o no se puede representar: la frase no se responde."""


def to_int(digits: str) -> int:
    """int() acotado: números enormes no desbordan ni fallan (los topes reales se aplican después)."""
    return int(digits) if len(digits) <= 9 else 10**9


def _custom(start: date, end: date) -> PeriodSpec:
    start, end = sorted((start, end))  # rango invertido -> se intercambia
    return PeriodSpec(preset="custom", from_date=start, to_date=end)


def _make_date(year: int, month: int, day: int) -> date:
    try:
        return date(year, month, day)
    except ValueError as exc:
        raise InvalidPeriod(str(exc)) from exc


def _year(text: str | None, month: int, today: date) -> int:
    """Año explícito, o el del mes más reciente con ese número cuyo primer día es <= hoy."""
    if text:
        y = to_int(text)
        return y + 2000 if len(text) == 2 else y
    return today.year if month <= today.month else today.year - 1


def _month_end(year: int, month: int) -> date:
    return (date(year + month // 12, month % 12 + 1, 1) - timedelta(days=1))


def bounds(spec: PeriodSpec, today: date) -> tuple[date, date]:
    """Primer y último día de un período (para saber si una referencia es el período inmediatamente anterior)."""
    if spec.preset == "custom":
        return spec.from_date, spec.to_date
    week_start, month_start = today - timedelta(days=today.weekday()), today.replace(day=1)
    quarter_start = date(today.year, 3 * ((today.month - 1) // 3) + 1, 1)
    last_month_end = month_start - timedelta(days=1)
    last_quarter_end = quarter_start - timedelta(days=1)
    months_back = (spec.n or 1) - 1
    y, m = divmod(today.year * 12 + today.month - 1 - months_back, 12)
    return {
        "today": (today, today), "yesterday": (today - timedelta(days=1),) * 2,
        "this_week": (week_start, today), "last_week": (week_start - timedelta(days=7), week_start - timedelta(days=1)),
        "this_month": (month_start, today), "last_month": (last_month_end.replace(day=1), last_month_end),
        "this_quarter": (quarter_start, today),
        "last_quarter": (date(last_quarter_end.year, last_quarter_end.month - 2, 1), last_quarter_end),
        "this_year": (date(today.year, 1, 1), today),
        "last_year": (date(today.year - 1, 1, 1), date(today.year - 1, 12, 31)),
        "last_n_days": (today - timedelta(days=(spec.n or 1) - 1), today),
        "last_n_months": (date(y, m + 1, 1), today),
    }[spec.preset]


def _last_n(n: int, unit: str, today: date) -> PeriodSpec:
    n = max(1, n)
    if unit.startswith("ano"):
        if n <= 3:
            return PeriodSpec(preset="last_n_months", n=n * 12)
        return _custom(today - timedelta(days=min(n * 365, MAX_DAYS) - 1), today)  # "últimos 5 años"
    if unit.startswith("mes"):
        return PeriodSpec(preset="last_n_months", n=min(n, 36))
    days = n * 7 if unit.startswith("semana") else n
    if days > 36:  # PeriodSpec.n <= 36 -> rango explícito
        return _custom(today - timedelta(days=min(days, MAX_DAYS) - 1), today)
    return PeriodSpec(preset="last_n_days", n=days)


def _dmy_range(m, today):
    d1, m1, y1, d2, m2, y2 = m.group(1, 2, 3, 4, 5, 6)
    m1, m2 = to_int(m1), to_int(m2)
    if not (1 <= m1 <= 12 and 1 <= m2 <= 12):
        raise InvalidPeriod("mes inválido")
    year1 = _year(y1, m1, today)
    year2 = _year(y2, m2, today) if y2 else (year1 if m2 >= m1 or y1 else year1 + 1)
    return _custom(_make_date(year1, m1, to_int(d1)), _make_date(year2, m2, to_int(d2)))


def _day(text: str) -> int:
    return 1 if text == "primero" else to_int(text)


def _dm_range(m, today):
    d1, mon1, d2, mon2, y = m.group(1, 2, 3, 4, 5)
    end_month = MONTHS[mon2]
    start_month = MONTHS[mon1] if mon1 else end_month
    year_start = _year(y, start_month, today)
    year_end = year_start if end_month >= start_month else year_start + 1
    if y and end_month < start_month:  # "del 20 de diciembre al 5 de enero de 2026": el año va con el final
        year_end, year_start = year_start, year_start - 1
    return _custom(_make_date(year_start, start_month, _day(d1)), _make_date(year_end, end_month, _day(d2)))


def _dmy_single(m, today):
    d, mon, y = m.group(1, 2, 3)
    mon = to_int(mon)
    if not 1 <= mon <= 12:
        raise InvalidPeriod("mes inválido")
    day = _make_date(_year(y, mon, today), mon, to_int(d))
    return _custom(day, day)


def _dm_single(m, today):
    d, mon, y = m.group(1, 2, 3)
    day = _make_date(_year(y, MONTHS[mon], today), MONTHS[mon], _day(d))
    return _custom(day, day)


def _named_month(m, today):
    mon = MONTHS[m.group(1)]
    year = _year(m.group(2) or m.group(3), mon, today)
    if not 1 <= year <= 9999:
        raise InvalidPeriod("año inválido")
    return _custom(date(year, mon, 1), _month_end(year, mon))


def _month_relative_year(m, today):
    mon, year = MONTHS[m.group(1)], today.year - (1 if m.group(3) else 0)
    return _custom(date(year, mon, 1), _month_end(year, mon))


def _year_only(m, today):
    year = to_int(m.group(1) or m.group(2))
    if not 1900 <= year <= 2100:
        raise InvalidPeriod("año fuera de rango")
    return _custom(date(year, 1, 1), date(year, 12, 31))


def _quarter(m, today):
    q = {"primer": 1, "segundo": 2, "tercer": 3, "cuarto": 4}[m.group(1)]
    start_month = 3 * q - 2
    year = _year(m.group(2), start_month, today)
    return _custom(date(year, start_month, 1), _month_end(year, start_month + 2))


def _weekday(m, today):
    day = today - timedelta(days=(today.weekday() - WEEKDAYS[m.group(1)]) % 7)
    return _custom(day, day)


def _preset(name):
    return lambda m, today: PeriodSpec(preset=name)


_SINGLE_LAST = {"semana": ("dia", 7), "mes": ("mes", 1), "trimestre": ("mes", 3), "semestre": ("mes", 6),
                "ano": ("mes", 12)}
_YEAR = r"(?: (?:de|del)(?: ano)? (\d{4}))?"
_DMY = r"(\d{1,2})/(\d{1,2})(?:/(\d{1,4}))?"

# (patrón, función(match, today) -> PeriodSpec). El orden importa: lo más específico primero.
PERIOD_RULES = [
    (rx(rf"(?:(?:del?|desde(?: el)?|entre(?: el)?) )?{_DMY} (?:al?|hasta(?: el)?|y(?: el)?|-) {_DMY}"), _dmy_range),
    (rx(rf"(?:del?|desde(?: el)?|entre(?: el)?) (\d{{1,2}}|primero)(?: de ({MONTH}))? (?:al?|hasta(?: el)?|y(?: el)?) "
        rf"(\d{{1,2}}) de ({MONTH}){_YEAR}"), _dm_range),
    (rx(rf"(?:(?:el|del|el dia|dia) )?{_DMY}"), _dmy_single),
    (rx(rf"(?:(?:el|del|el dia|dia) )?(\d{{1,2}}|primero) de ({MONTH}){_YEAR}"), _dm_single),
    (rx(r"(?:(?:en|durante|de|para|por) )?(?:(?:los|las) )?(?:ultim[oa]s (\d+)|(\d+) ultim[oa]s) "
        r"(dias?|semanas?|mes(?:es)?|anos?)"),
     lambda m, today: _last_n(to_int(m.group(1) or m.group(2)), m.group(3), today)),
    (rx(r"(?:(?:en|durante|de|del|para) )?(?:(?:el|la) )?ultim[oa] (semana|mes|trimestre|semestre|ano)"),
     lambda m, today: _last_n(_SINGLE_LAST[m.group(1)][1], _SINGLE_LAST[m.group(1)][0], today)),
    (rx(rf"(?:el )?(primer|segundo|tercer|cuarto) trimestre{_YEAR}"), _quarter),
    (rx(r"(?:del |el )?dia de hoy|hoy|del dia|en el dia|lo que va del dia"), _preset("today")),
    (rx(r"anteayer|antier|antes de (?:ayer|anoche)"),
     lambda m, today: _custom(today - timedelta(days=2), today - timedelta(days=2))),
    (rx(r"(?:(?:del|el) dia de )?ayer|anoche"), _preset("yesterday")),
    (rx(rf"(?:(?:el|todo el) )?(?:mes de )?({MONTH}) (?:de|del) (?:(este|el presente) ano|ano (pasado|anterior))"),
     _month_relative_year),
    (rx(r"(?:esta|la presente) semana|(?:la )?semana (?:actual|en curso)|lo que va de (?:la|esta) semana"),
     _preset("this_week")),
    (rx(r"(?:la )?semana (?:pasada|anterior|que paso)|la pasada semana"), _preset("last_week")),
    (rx(r"(?:este|el presente) mes|(?:el )?mes (?:actual|en curso)|lo que va del? (?:este )?mes"), _preset("this_month")),
    (rx(r"(?:el )?mes (?:pasado|anterior|que paso)|el pasado mes"), _preset("last_month")),
    (rx(r"(?:este|el presente) trimestre|(?:el )?trimestre (?:actual|en curso)|lo que va del trimestre"),
     _preset("this_quarter")),
    (rx(r"(?:el )?trimestre (?:pasado|anterior)"), _preset("last_quarter")),
    (rx(r"(?:este|el presente) ano|(?:el )?ano (?:actual|en curso)|lo que va del? (?:este )?ano|esta gestion|"
        r"(?:la )?gestion actual"), _preset("this_year")),
    (rx(r"(?:el )?ano (?:pasado|anterior|que paso)|el pasado ano|(?:la )?gestion (?:pasada|anterior)"), _preset("last_year")),
    (rx(rf"(?:(?:el|todo el) )?(?:mes de )?({MONTH})(?: (?:de|del)(?: ano)? (\d{{4}})| (\d{{4}}))?"), _named_month),
    (rx(r"(?:el |la )?(?:ano|gestion) (\d{4})|(?:en|durante|del|de) (\d{4})"), _year_only),
    (rx(rf"(?:(?:el|este|del|de este) )?({WEEKDAY})(?: (?:pasado|anterior))?"), _weekday),
    # "ventas de la semana / del mes / del año" = la semana, el mes o el año en curso (van al final: "del mes de
    # agosto" y "la semana pasada" ya se consumieron)
    (rx(r"(?:de|en) (?:la|esta) semana"), _preset("this_week")),
    (rx(r"(?:del|en el) mes"), _preset("this_month")),
    (rx(r"(?:del|en el) trimestre"), _preset("this_quarter")),
    (rx(r"(?:del|en el) ano"), _preset("this_year")),
]
