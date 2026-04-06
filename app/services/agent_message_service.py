from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.agent_message import AgentMessage
from app.schemas.agent_message import AgentMessageCreate, AgentMessageUpdate


async def create_message(db: AsyncSession, message_create: AgentMessageCreate) -> AgentMessage:
    message = AgentMessage(
        sender_id=message_create.sender_id,
        recipient_id=message_create.recipient_id,
        content=message_create.content,
        message_type=message_create.message_type,
        priority=message_create.priority
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


async def get_message(db: AsyncSession, message_id: str) -> AgentMessage | None:
    result = await db.execute(select(AgentMessage).where(AgentMessage.message_id == message_id))
    return result.scalar_one_or_none()


async def get_messages_for_recipient(
    db: AsyncSession, 
    recipient_id: str, 
    unread_only: bool = False,
    limit: int = 50
) -> list[AgentMessage]:
    query = select(AgentMessage).where(AgentMessage.recipient_id == recipient_id)
    if unread_only:
        query = query.where(AgentMessage.read.is_(False))
    query = query.order_by(AgentMessage.timestamp.desc()).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_messages_from_sender(
    db: AsyncSession, 
    sender_id: str, 
    limit: int = 50
) -> list[AgentMessage]:
    result = await db.execute(
        select(AgentMessage)
        .where(AgentMessage.sender_id == sender_id)
        .order_by(AgentMessage.timestamp.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def update_message(
    db: AsyncSession, 
    message_id: str, 
    update: AgentMessageUpdate
) -> AgentMessage | None:
    result = await db.execute(select(AgentMessage).where(AgentMessage.message_id == message_id))
    message = result.scalar_one_or_none()
    if message:
        message.delivered = update.delivered
        message.read = update.read
        await db.commit()
        await db.refresh(message)
    return message


async def mark_all_delivered(db: AsyncSession, recipient_id: str) -> int:
    """Mark all undelivered messages as delivered. Returns count updated."""
    result = await db.execute(
        select(AgentMessage).where(
            and_(AgentMessage.recipient_id == recipient_id, AgentMessage.delivered.is_(False))
        )
    )
    messages = result.scalars().all()
    for message in messages:
        message.delivered = True
    await db.commit()
    return len(list(messages))
