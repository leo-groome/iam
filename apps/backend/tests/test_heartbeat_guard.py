"""IAM-005: el avance acreditado lo limita el tiempo real, no lo que afirma el cliente."""

from __future__ import annotations

from app.services.heartbeat_guard import credited_pdf_page, credited_video_pct


def test_video_jump_is_capped_by_elapsed_time():
    # Primer heartbeat: pos=100% de un video de 100 s → solo se acredita el margen (2 s).
    assert credited_video_pct(0, 100, 100, None) == 2
    # 10 s reales después → a lo sumo 1.5x10 + 2 s más.
    assert credited_video_pct(2, 100, 100, 10) == 19
    # Un heartbeat con pos menor nunca baja el avance.
    assert credited_video_pct(50, 100, 10, 5) == 50
    # Reproducción normal (1x) siempre se acredita completa.
    assert credited_video_pct(10, 100, 15, 5) == 15


def test_pdf_pages_capped_by_total_and_time():
    assert credited_pdf_page(0, 1, 99, None) == 1  # last_page > total se recorta
    assert credited_pdf_page(0, 10, 10, None) == 1  # sin tiempo previo: 1 página
    assert credited_pdf_page(1, 10, 10, 0.2) == 1  # ráfaga <1 s: nada
    assert credited_pdf_page(1, 10, 10, 6) == 4  # 6 s → 3 páginas (≥2 s por página)
