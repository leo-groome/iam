"""Reglas anti-trampa para heartbeats de progreso (IAM-005).

Funciones puras: el avance acreditado nunca supera lo que el tiempo real permite.
"""

from __future__ import annotations

# Un alumno puede avanzar como mucho 1.5x la velocidad real (reproducción acelerada) + margen.
_VIDEO_SPEED_FACTOR = 1.5
_VIDEO_SLACK_SECONDS = 2.0
_PDF_MIN_SECONDS_PER_PAGE = 2.0


def credited_video_pct(
    prev_pct: int, duration: int | None, pos: int, elapsed_seconds: float | None
) -> int:
    """% de video acreditado dado el avance previo, la posición reportada y el tiempo real."""
    if duration is None or duration <= 0:
        return prev_pct
    prev_credit = duration * prev_pct / 100
    if pos <= prev_credit:
        return prev_pct
    allowance = _VIDEO_SLACK_SECONDS + _VIDEO_SPEED_FACTOR * max(0.0, elapsed_seconds or 0.0)
    credit = min(float(pos), prev_credit + allowance)
    return max(prev_pct, min(100, round(credit / duration * 100)))


def credited_pdf_page(
    prev_page: int, total_pages: int, reported_page: int, elapsed_seconds: float | None
) -> int:
    """Última página acreditada: acotada al total real y a ≥2 s por página."""
    page = min(reported_page, total_pages)
    if page <= prev_page:
        return prev_page
    if elapsed_seconds is None:
        allowed = 1
    elif elapsed_seconds < 1:
        allowed = 0
    else:
        allowed = max(1, int(elapsed_seconds // _PDF_MIN_SECONDS_PER_PAGE))
    return min(page, prev_page + allowed)
