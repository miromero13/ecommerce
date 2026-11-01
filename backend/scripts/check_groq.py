"""Prueba manual de Groq: python -m scripts.check_groq [--phrases ARCHIVO.json] (desde backend/). Nunca imprime la clave.

--phrases: lista JSON de frases (texto u objetos con la clave "phrase"); una línea por frase, catálogo vacío,
2.5 s entre llamadas y máximo 40 frases por corrida (la cuota gratuita es limitada). No lista los modelos.
"""
import argparse
import json
import time
from datetime import date
from uuid import uuid4

import httpx

from app.core.config import settings
from app.services.report_interpreter import Catalog
from app.services.report_llm_fallback import interpret_with_groq

MAX_PHRASES, PAUSE = 40, 2.5


def load_phrases(path: str) -> list[str]:
    with open(path, encoding="utf-8") as file:
        items = json.load(file)
    return [item["phrase"] if isinstance(item, dict) else item for item in items][:MAX_PHRASES]


def run_batch(phrases, interpret=interpret_with_groq, sleep=time.sleep, out=print) -> None:
    for index, phrase in enumerate(phrases[:MAX_PHRASES]):
        if index:
            sleep(PAUSE)
        spec = interpret(phrase, Catalog(), uuid4(), date.today())
        result = f"OK {spec.kind}/{spec.metric}/{'+'.join(spec.group_by)}/{spec.period.preset}" if spec else "None"
        out(f"{phrase} -> {result}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phrases", help="archivo JSON con frases para probar en lote")
    args = parser.parse_args()
    if not settings.groq_api_key:
        raise SystemExit("No hay GROQ_API_KEY configurada en backend/.env; solo se usa el intérprete local.")
    if args.phrases:
        return run_batch(load_phrases(args.phrases))
    try:
        reply = httpx.get(f"{settings.groq_base_url}/models", timeout=settings.groq_timeout_seconds,
                          headers={"Authorization": f"Bearer {settings.groq_api_key}"})
        reply.raise_for_status()
        print("Modelos disponibles (elige uno para GROQ_MODEL):")
        for model in sorted(item["id"] for item in reply.json().get("data", [])):
            print(" -", model)
    except Exception as error:
        print(f"No se pudo listar los modelos ({type(error).__name__}).")

    print(f"\nModelo configurado: {settings.groq_model}")
    phrase = "como le fue al negocio en los ultimos 3 meses, ingresos por mes"
    spec = interpret_with_groq(phrase, Catalog(), uuid4(), date.today())
    print(f"Frase: {phrase}")
    print(spec.model_dump_json(indent=2) if spec else "no se pudo interpretar")


if __name__ == "__main__":
    main()
