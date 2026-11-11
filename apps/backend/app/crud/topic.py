from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.course import ContentBlock, Module, Topic
from app.models.progress import ContentBlockProgress, TopicProgress
from app.models.user import User

if TYPE_CHECKING:
    from app.schemas.admin.topics import ContentBlockIn


async def get_topic_with_module(db: AsyncSession, topic_id: uuid.UUID) -> Topic | None:
    stmt = (
        select(Topic)
        .where(Topic.id == topic_id)
        .options(
            selectinload(Topic.module).selectinload(Module.topics),
            selectinload(Topic.blocks),
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_or_create_progress(
    db: AsyncSession, user: User, topic: Topic
) -> TopicProgress:
    stmt = select(TopicProgress).where(
        TopicProgress.user_id == user.id,
        TopicProgress.topic_id == topic.id,
    )
    result = await db.execute(stmt)
    tp = result.scalar_one_or_none()
    if tp is None:
        tp = TopicProgress(
            user_id=user.id,
            topic_id=topic.id,
            state="bloqueado",
        )
        db.add(tp)
        await db.flush()
    return tp


async def get_or_create_block_progress(
    db: AsyncSession, user: User, block: ContentBlock
) -> ContentBlockProgress:
    stmt = select(ContentBlockProgress).where(
        ContentBlockProgress.user_id == user.id,
        ContentBlockProgress.block_id == block.id,
    )
    result = await db.execute(stmt)
    bp = result.scalar_one_or_none()
    if bp is None:
        bp = ContentBlockProgress(
            user_id=user.id,
            block_id=block.id,
        )
        db.add(bp)
        await db.flush()
    return bp


_REQUIRED_KINDS = ("video", "pdf")


async def replace_topic_blocks(
    db: AsyncSession, topic: Topic, blocks_in: list[ContentBlockIn]
) -> None:
    """Sincroniza los bloques del tema con la lista recibida (upsert por `id`).

    - Bloque con `id` existente: se actualiza en sitio y conserva su progreso
      (`ContentBlockProgress`), salvo que cambie `kind` o `media_key` (contenido
      distinto: el progreso ya no aplica y se borra).
    - Bloque sin `id` (o con `id` ajeno): se crea nuevo.
    - Bloque existente omitido: se borra junto con su progreso (borrado explícito,
      SQLite en tests no aplica ON DELETE CASCADE).

    Re-gating: si se creó o reemplazó un bloque requerido (video/pdf), los
    alumnos en `contenido_visto`/`en_repaso` vuelven a `disponible` para ver el
    contenido nuevo. `aprobado` y `bloqueado` no se tocan. Editar texto, orden o
    metadatos NO resetea a nadie. Todo en la transacción del caller (él hace commit).
    Sincroniza `topic.content_type` con el kind del primer bloque.
    Caller garantiza `blocks_in` no vacío.
    """
    existing = {b.id: b for b in topic.blocks}
    kept: set[uuid.UUID] = set()
    regate = False
    drop_progress: list[uuid.UUID] = []

    for idx, block_in in enumerate(blocks_in):
        block = existing.get(block_in.id) if block_in.id is not None else None
        if block is None or block.id in kept:
            db.add(
                ContentBlock(
                    topic_id=topic.id,
                    kind=block_in.kind,
                    media_key=block_in.media_key,
                    content_body=block_in.content_body,
                    duration_seconds=block_in.duration_seconds,
                    order_index=idx,
                )
            )
            regate = regate or block_in.kind in _REQUIRED_KINDS
            continue
        kept.add(block.id)
        content_changed = block.kind != block_in.kind or block.media_key != block_in.media_key
        if content_changed:
            block.pdf_total_pages = None  # se recuenta en el servidor con el archivo nuevo
            drop_progress.append(block.id)
            regate = regate or block_in.kind in _REQUIRED_KINDS
        block.kind = block_in.kind
        block.media_key = block_in.media_key
        block.content_body = block_in.content_body
        block.duration_seconds = block_in.duration_seconds
        block.order_index = idx

    removed = [bid for bid in existing if bid not in kept]
    drop_progress.extend(removed)
    if drop_progress:
        await db.execute(
            delete(ContentBlockProgress).where(ContentBlockProgress.block_id.in_(drop_progress))
        )
    if removed:
        await db.execute(delete(ContentBlock).where(ContentBlock.id.in_(removed)))

    topic.content_type = blocks_in[0].kind

    if regate:
        await db.execute(
            update(TopicProgress)
            .where(
                TopicProgress.topic_id == topic.id,
                TopicProgress.state.in_(("contenido_visto", "en_repaso")),
            )
            .values(state="disponible", content_completed_at=None)
        )
    await db.flush()
