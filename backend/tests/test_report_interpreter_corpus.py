import json
from pathlib import Path

from tests.corpus_eval import accuracy_table, evaluate

DEV = Path(__file__).parent / "data" / "report_phrases_dev.json"


def test_dev_corpus_accuracy():
    results = evaluate(json.loads(DEV.read_text(encoding="utf-8")))
    print("\n" + accuracy_table(results))
    failures = [r for r in results if not r["ok"]]
    for r in failures:
        print(f"FAIL {r['id']} {r['phrase']!r}: {r['reason']} | got={r['got']}")
    accuracy = 1 - len(failures) / len(results)
    none_entries = [r for r in results if r["must_return_none"]]
    assert all(r["ok"] for r in none_entries), [r["id"] for r in none_entries if not r["ok"]]
    assert accuracy >= 0.97, f"{accuracy:.1%}"
