"""CU08: respaldo con Groq (la red se reemplaza por un doble; nunca se llama a la red real)."""
import json
import logging

import httpx
import pytest

from test_analytics_routes import ENGINEER_PHRASE, NOT_UNDERSTOOD, reports_api, sold  # noqa: F401
from test_catalog_tenant_isolation import catalog  # noqa: F401
from test_employee_authorization import headers
from test_marketplace_transactions import call, market  # noqa: F401

KEY = "gsk_TEST_SECRET_KEY_123"
ODD = "como le fue al negocio en la ultima temporada"
GOOD = {"metric": "revenue", "group_by": ["month"], "period": {"preset": "this_year"}}


class Groq:
    """Doble de report_llm_fallback._post: guarda las llamadas y responde lo configurado."""
    def __init__(self):
        self.calls, self.reply = [], None

    def __call__(self, body):
        self.calls.append(body)
        if isinstance(self.reply, Exception):
            raise self.reply
        request = httpx.Request("POST", "http://groq.test")
        if isinstance(self.reply, int):
            return httpx.Response(self.reply, json={"error": "x"}, request=request)
        content = self.reply if isinstance(self.reply, str) else json.dumps(self.reply)
        return httpx.Response(200, json={"choices": [{"message": {"content": content}}]}, request=request)


@pytest.fixture(autouse=True)
def _logger_enabled():
    """Otras pruebas (p. ej. fileConfig de Alembic) pueden desactivar loggers ya creados; caplog no capturaría nada."""
    log = logging.getLogger("app.services.report_llm_fallback")
    log.disabled, log.propagate = False, True
    yield


@pytest.fixture
def groq(monkeypatch):
    from app.core.config import settings
    from app.services import report_llm_fallback as module
    fake = Groq()
    fake.reply = GOOD
    monkeypatch.setattr(settings, "groq_api_key", KEY)
    monkeypatch.setattr(module, "_post", fake)
    module._calls.clear(), module._global_calls.clear()
    yield fake
    module._calls.clear(), module._global_calls.clear()


def ask(api, user, text=ODD):
    return api.post("/api/reports/query", headers=headers(user), json={"query": text})


def assert_not_understood(result):
    assert result.status_code == 422, result.text
    assert result.json() == {"statusCode": 422, "message": NOT_UNDERSTOOD, "error": NOT_UNDERSTOOD}


def test_local_interpretation_wins_without_calling_groq(reports_api, market, groq):
    data = call(reports_api, market.staff[0, "administrador"], "POST", "/reports/query",
                json={"query": ENGINEER_PHRASE})
    assert data["interpreted_by"] == "local" and groq.calls == []


def test_groq_is_used_when_local_does_not_understand(reports_api, market, groq):
    data = call(reports_api, market.staff[0, "administrador"], "POST", "/reports/query", json={"query": ODD})
    assert data["interpreted_by"] == "groq" and len(groq.calls) == 1
    assert data["spec"]["metric"] == "revenue" and data["spec"]["group_by"] == ["month"]
    assert data["spec"]["period"]["preset"] == "this_year"


def test_without_key_groq_is_never_called(reports_api, market, groq, monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "groq_api_key", None)
    assert_not_understood(ask(reports_api, market.staff[0, "administrador"]))
    assert groq.calls == []


@pytest.mark.parametrize("reply", [
    "esto no es json", "respuesta sin llaves", '{"metric": "units"', {"metric": "bitcoin", "period": {}},
    {"metric": "units", "group_by": ["day", "month"], "period": {"preset": "today"}},
    {"metric": "units"}, 429, 500, 401, 404, httpx.ReadTimeout("t"), httpx.ConnectError("c"),
])
def test_groq_failures_degrade_to_422_with_examples(reports_api, market, groq, reply):
    groq.reply = reply
    assert_not_understood(ask(reports_api, market.staff[0, "administrador"]))
    assert len(groq.calls) == 1  # sin reintentos


def test_json_wrapped_in_code_fences_is_accepted(reports_api, market, groq):
    groq.reply = "Claro:\n```json\n" + json.dumps(GOOD) + "\n```\nListo."
    data = call(reports_api, market.staff[0, "administrador"], "POST", "/reports/query", json={"query": ODD})
    assert data["interpreted_by"] == "groq"


@pytest.mark.parametrize("field,label", [("branch_ids", "sucursal"), ("product_ids", "producto"),
                                         ("category_ids", "categoría")])
def test_foreign_ids_from_groq_are_rejected(reports_api, sold, groq, field, label):
    foreign = {"branch_ids": sold.branches[2], "product_ids": sold.foreign.product,
               "category_ids": sold.foreign.category}[field]
    groq.reply = {**GOOD, field: [str(foreign.id)]}
    result = ask(reports_api, sold.staff[0, "administrador"])
    assert result.status_code == 422 and f"No se encontró en el catálogo: {label}" in result.json()["message"]
    assert not result.json().get("data")


def test_own_ids_from_groq_are_accepted(reports_api, sold, groq):
    groq.reply = {**GOOD, "branch_ids": [str(sold.branches[0].id)]}
    data = call(reports_api, sold.staff[0, "administrador"], "POST", "/reports/query", json={"query": ODD})
    assert data["spec"]["branch_ids"] == [str(sold.branches[0].id)]


def test_request_to_groq_carries_only_sentence_date_and_own_catalog(reports_api, sold, groq, caplog):
    from datetime import date
    caplog.set_level(logging.DEBUG, logger="app.services.report_llm_fallback")
    ask(reports_api, sold.staff[0, "administrador"])
    (body,) = groq.calls
    assert KEY not in json.dumps(body)
    assert body["response_format"] == {"type": "json_object"} and body["temperature"] == 0
    sent = "\n".join(m["content"] for m in body["messages"])
    assert f"<request>{ODD}</request>" in sent and date.today().isoformat() in sent
    own = [sold.branches[0], sold.branches[1], sold.own.product, sold.own.category]
    assert all(str(item.id) in sent and item.name.lower() in sent for item in own)
    for item in (sold.branches[2], sold.foreign.product, sold.foreign.category):
        assert str(item.id) not in sent and f"-> {item.name.lower()}" not in sent
    for secret in ("snapshot", "total_amount", "unit_price"):
        assert secret not in sent
    for rule in ("last_n_months", "revenue", "payment_method", "table", "SQL"):
        assert rule in sent
    assert KEY not in caplog.text and ODD not in caplog.text


def test_failure_logs_never_contain_key_or_sentence(reports_api, market, groq, caplog):
    groq.reply = 429
    caplog.set_level(logging.DEBUG, logger="app.services.report_llm_fallback")
    ask(reports_api, market.staff[0, "administrador"])
    assert "429" in caplog.text and KEY not in caplog.text and ODD not in caplog.text


def test_key_travels_only_in_authorization_header(monkeypatch):
    from app.core.config import settings
    from app.services import report_llm_fallback as module
    seen = []
    client = httpx.Client(transport=httpx.MockTransport(lambda req: seen.append(req) or httpx.Response(200, json={})))
    monkeypatch.setattr(settings, "groq_api_key", KEY)
    monkeypatch.setattr(module.httpx, "post", client.post)
    module._post({"model": "m"})
    assert seen[0].headers["authorization"] == f"Bearer {KEY}" and KEY not in seen[0].content.decode()
    assert str(seen[0].url) == f"{settings.groq_base_url}/chat/completions"


def test_quota_guard_is_per_tenant(reports_api, market, groq, monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "groq_max_calls_per_tenant_hour", 2)
    admin = market.staff[0, "administrador"]
    assert [ask(reports_api, admin).status_code for _ in range(3)] == [200, 200, 422]
    assert len(groq.calls) == 2
    other = market.staff[2, "administrador"]  # empresa ajena: su propio cupo
    assert ask(reports_api, other).status_code == 200 and len(groq.calls) == 3


def test_manager_still_gets_forced_branch_with_groq(reports_api, sold, groq):
    manager = sold.staff[0, "encargado"]
    groq.reply = {**GOOD, "branch_ids": [str(sold.branches[1].id)]}
    data = call(reports_api, manager, "POST", "/reports/query", json={"query": ODD})
    assert data["interpreted_by"] == "groq" and data["spec"]["branch_ids"] == [str(sold.branches[0].id)]


def test_allow_is_thread_safe_and_never_raises(groq, monkeypatch):
    import threading
    from datetime import date
    from uuid import uuid4
    from app.core.config import settings
    from app.services import report_llm_fallback as module
    from app.services.report_interpreter import Catalog
    monkeypatch.setattr(settings, "groq_max_calls_per_tenant_hour", 5)
    tenant, errors, barrier = uuid4(), [], threading.Barrier(20)

    def work():
        try:
            barrier.wait()
            module.interpret_with_groq(ODD, Catalog(), tenant, date.today())
        except Exception as error:  # pragma: no cover
            errors.append(error)

    threads = [threading.Thread(target=work) for _ in range(20)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert errors == [] and len(groq.calls) == 5


def test_global_limit_applies_across_tenants(reports_api, market, groq, monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "groq_max_calls_per_hour_global", 1)
    assert ask(reports_api, market.staff[0, "administrador"]).status_code == 200
    assert_not_understood(ask(reports_api, market.staff[2, "administrador"]))
    assert len(groq.calls) == 1


def test_denied_call_logs_tenant_only(groq, monkeypatch, caplog):
    from datetime import date
    from uuid import uuid4
    from app.core.config import settings
    from app.services import report_llm_fallback as module
    from app.services.report_interpreter import Catalog
    monkeypatch.setattr(settings, "groq_max_calls_per_tenant_hour", 1)
    tenant = uuid4()
    caplog.set_level(logging.INFO, logger="app.services.report_llm_fallback")
    module.interpret_with_groq(ODD, Catalog(), tenant, date.today())
    module.interpret_with_groq(ODD, Catalog(), tenant, date.today())
    assert str(tenant) in caplog.text and ODD not in caplog.text and KEY not in caplog.text


def test_catalog_is_capped_and_matching_product_is_kept(groq):
    from datetime import date
    from uuid import uuid4
    from app.services import report_llm_fallback as module
    from app.services.report_interpreter import Catalog
    products = {f"producto {n:03d}": uuid4() for n in range(500)}
    products["zapatilla roja"] = target = uuid4()
    module.interpret_with_groq("ventas de zapatilla", Catalog(products=products), uuid4(), date.today())
    user = groq.calls[0]["messages"][1]["content"]
    listed = [line for line in user.split("Productos (id -> nombre):")[1].splitlines() if " -> " in line]
    assert len(listed) <= 60 and f"{target} -> zapatilla roja" in listed


# --- palabras que el intérprete local no aplicó (ronda de correcciones 1) ---------------------------------------
UNKNOWN_WORDS = "ventas de zapatos"


def test_clean_phrase_has_no_warnings(reports_api, market, groq):
    data = call(reports_api, market.staff[0, "administrador"], "POST", "/reports/query",
                json={"query": ENGINEER_PHRASE})
    assert data["warnings"] == [] and groq.calls == []


def test_ignored_words_try_groq_first_and_its_spec_wins(reports_api, market, groq):
    data = call(reports_api, market.staff[0, "administrador"], "POST", "/reports/query",
                json={"query": UNKNOWN_WORDS})
    assert data["interpreted_by"] == "groq" and len(groq.calls) == 1 and data["warnings"] == []
    assert data["spec"]["group_by"] == ["month"]


def test_ignored_words_without_groq_keep_the_local_spec_with_a_warning(reports_api, market, groq, monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "groq_api_key", None)
    data = call(reports_api, market.staff[0, "administrador"], "POST", "/reports/query",
                json={"query": UNKNOWN_WORDS})
    assert data["interpreted_by"] == "local" and groq.calls == []
    assert data["warnings"] == ["No apliqué estas palabras: «zapatos»."]
    assert data["spec"]["metric"] == "revenue" and data["spec"]["product_ids"] == []


@pytest.mark.parametrize("reply", [500, "esto no es json", {"metric": "bitcoin", "period": {}}])
def test_ignored_words_when_groq_fails_keep_the_local_spec_with_a_warning(reports_api, market, groq, reply):
    groq.reply = reply
    data = call(reports_api, market.staff[0, "administrador"], "POST", "/reports/query",
                json={"query": "ventas de zapatos y carteras por favor"})
    assert data["interpreted_by"] == "local" and len(groq.calls) == 1
    assert data["warnings"] == ["No apliqué estas palabras: «zapatos», «carteras»."]


# --- R5: tipos nuevos, ejemplos de pocos disparos y red de seguridad --------------------------------------------
def _fixed_prompt(today=None):
    from datetime import date
    from app.services import report_llm_fallback as module
    return module._system_prompt(today or date(2026, 11, 11))


def _direct(groq, reply, text=ODD):
    from datetime import date
    from uuid import uuid4
    from app.services import report_llm_fallback as module
    from app.services.report_interpreter import Catalog
    groq.reply = reply
    return module.interpret_with_groq(text, Catalog(), uuid4(), date.today())


def test_system_prompt_mentions_new_kinds_presets_and_stays_small():
    prompt = _fixed_prompt()
    for word in ("critical_stock", "movements", "inventory", "customers", "customer", "last_week", "this_quarter",
                 "last_quarter", "last_year", "custom", "from_date", "unsupported", "compare_previous"):
        assert word in prompt
    assert len(prompt) <= 9000


@pytest.mark.parametrize("today", [__import__("datetime").date(2026, 11, 11), __import__("datetime").date(2027, 3, 2)])
def test_few_shot_examples_are_enough_and_all_validate(today):
    from app.schemas.analytics_schema import AnalyticsQuery
    from app.services import report_llm_fallback as module
    examples = module.examples_for(today)
    assert len(examples) >= 10
    prompt = _fixed_prompt(today)
    for request, answer in examples:
        assert request in prompt and json.dumps(answer, ensure_ascii=False, separators=(",", ":")) in prompt
        if answer != {"unsupported": True}:
            AnalyticsQuery.model_validate(answer)
    assert any(answer == {"unsupported": True} for _, answer in examples)


def test_example_dates_follow_today_across_year_boundary():
    from datetime import date
    prompt_a, prompt_b = _fixed_prompt(date(2026, 11, 11)), _fixed_prompt(date(2027, 3, 2))
    assert "ventas de octubre por categoría" in prompt_a and '"from_date":"2026-10-01","to_date":"2026-10-31"' in prompt_a
    assert "el lunes" in prompt_a and '"from_date":"2026-11-09","to_date":"2026-11-09"' in prompt_a
    assert "ventas de febrero por categoría" in prompt_b and '"from_date":"2027-02-01","to_date":"2027-02-28"' in prompt_b
    assert "el lunes" in prompt_b and '"from_date":"2027-03-01","to_date":"2027-03-01"' in prompt_b
    assert "del 3 al 10 de febrero" in prompt_b and '"from_date":"2027-02-03","to_date":"2027-02-10"' in prompt_b
    assert "2026-11-11" not in prompt_b


def test_year_boundary_last_month_is_december():
    from datetime import date
    prompt = _fixed_prompt(date(2027, 1, 5))
    assert "ventas de diciembre" in prompt and '"from_date":"2026-12-01","to_date":"2026-12-31"' in prompt


def test_unsupported_answer_is_none_and_logs_nothing_sensitive(groq, caplog):
    caplog.set_level(logging.DEBUG, logger="app.services.report_llm_fallback")
    assert _direct(groq, {"unsupported": True}) is None
    assert ODD not in caplog.text and KEY not in caplog.text and "falló" not in caplog.text


def test_non_sales_kind_is_normalized_to_defaults(groq):
    spec = _direct(groq, {"kind": "inventory", "metric": "revenue", "group_by": ["branch", "branch"], "top_n": 3,
                          "order": "asc", "channel": "online", "payment_methods": ["qr"], "compare_previous": True,
                          "chart": "donut", "period": {"preset": "today"}})
    assert (spec.kind, spec.metric, spec.group_by, spec.top_n, spec.order) == ("inventory", "units", ["product"], None, "desc")
    assert (spec.channel, spec.payment_methods, spec.compare_previous, spec.chart) == ("all", [], False, None)
    assert spec.period.preset == "today"


def test_non_sales_kind_keeps_filters(groq):
    from uuid import uuid4
    branch = str(uuid4())
    spec = _direct(groq, {"kind": "movements", "branch_ids": [branch], "metric": "orders", "period": {"preset": "last_week"}})
    assert spec.branch_ids[0].hex == branch.replace("-", "") and spec.metric == "units"


def test_custom_period_with_iso_dates_is_accepted(groq):
    spec = _direct(groq, {"metric": "revenue", "group_by": [], "period": {"preset": "custom", "from_date": "2026-10-01",
                                                                           "to_date": "2026-10-31"}})
    assert spec.period.preset == "custom" and spec.period.to_date.isoformat() == "2026-10-31"


def test_duplicate_dimensions_are_dropped_for_sales(groq):
    spec = _direct(groq, {"group_by": ["product", "product"], "period": {}})
    assert spec.group_by == ["product"]


def test_check_groq_batch_caps_pauses_and_prints_one_line_each(tmp_path):
    from app.schemas.analytics_schema import AnalyticsQuery
    from scripts import check_groq
    path = tmp_path / "p.json"
    path.write_text(json.dumps(["uno", {"phrase": "dos"}] + [f"f{n}" for n in range(60)]), encoding="utf-8")
    phrases = check_groq.load_phrases(str(path))
    assert len(phrases) == 40 and phrases[:2] == ["uno", "dos"]
    spec = AnalyticsQuery.model_validate({"metric": "revenue", "group_by": ["branch"], "period": {"preset": "today"}})
    asked, sleeps, lines = [], [], []

    def interpret(text, catalog, tenant, today):
        asked.append((text, catalog.products, catalog.branches))
        return spec if text == "uno" else None

    check_groq.run_batch(phrases, interpret, sleeps.append, lines.append)
    assert len(lines) == 40 and len(sleeps) == 39 and set(sleeps) == {2.5}
    assert lines[0] == "uno -> OK sales/revenue/branch/today" and lines[1] == "dos -> None"
    assert all(not products and not branches for _, products, branches in asked)


@pytest.mark.parametrize("model,effort", [("openai/gpt-oss-20b", True), ("openai/gpt-oss-120b", True),
                                          ("qwen/qwen3.8-27b", False), ("llama-3.3-70b-versatile", False)])
def test_request_body_depends_on_model(monkeypatch, model, effort):
    from datetime import date
    from app.core.config import settings
    from app.services import report_llm_fallback as module
    from app.services.report_interpreter import Catalog
    monkeypatch.setattr(settings, "groq_model", model)
    body = module._request_body(ODD, Catalog(), date(2026, 11, 11))
    assert body["max_tokens"] == 1500 and body["model"] == model and body["temperature"] == 0
    assert ("reasoning_effort" in body) is effort
    if effort:
        assert body["reasoning_effort"] == "low"


@pytest.mark.parametrize("today", [__import__("datetime").date(2026, 11, 11), __import__("datetime").date(2027, 3, 2)])
def test_round4_rules_examples_and_size_cap(today):
    from app.schemas.analytics_schema import AnalyticsQuery
    from app.services import report_llm_fallback as module
    prompt = _fixed_prompt(today)
    assert len(prompt) <= 6500
    for rule in ("invierno", "temporada", "NUNCA inventes fechas", "dos períodos con nombre", "nunca units",
                 "más de una vez", "me quedan"):
        assert rule in prompt
    examples = dict(module.examples_for(today))
    assert any("me quedan" in request and a["kind"] == "inventory" and not a.get("product_ids")
               for request, a in examples.items())
    assert any("comparame" in request and a["compare_previous"] is True and a["period"]["preset"] == "custom"
               for request, a in examples.items())
    assert any(a == {"unsupported": True} for a in examples.values()) and len(examples) >= 10
    for answer in examples.values():
        if answer != {"unsupported": True}:
            AnalyticsQuery.model_validate(answer)
