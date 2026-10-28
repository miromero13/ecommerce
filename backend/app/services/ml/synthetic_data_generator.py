"""Reproducible training samples, never persisted as business records."""
from datetime import date, timedelta

import numpy as np


def synthetic_weeks(end: date, count: int = 64) -> dict[date, float]:
    rng = np.random.default_rng(42)
    start = end - timedelta(weeks=count)
    return {
        start + timedelta(weeks=i): max(0.0, 100 + 0.35 * i + 24 * np.sin(2 * np.pi * i / 52) + rng.normal(0, 4))
        for i in range(count)
    }


def synthetic_customers() -> list[tuple[float, float, float]]:
    rng = np.random.default_rng(42)
    centers = [(10, 18, 3000), (75, 6, 650), (200, 1, 90)]
    return [
        tuple(np.maximum([0, 1, 1], rng.normal(center, [8, 1.2, center[2] * 0.12])))
        for center in centers for _ in range(20)
    ]


def source_metadata(real: int, synthetic: int) -> dict:
    mode = 'mixed' if real and synthetic else 'real' if real else 'synthetic'
    notice = (
        'Datos reales del negocio; las métricas no garantizan resultados futuros.' if mode == 'real' else
        'Demostración con datos sintéticos' + (' combinados con datos reales.' if real else '; no representa ventas ni clientes reales.')
    )
    return {'mode': mode, 'real_samples': real, 'synthetic_samples': synthetic, 'notice': notice}
