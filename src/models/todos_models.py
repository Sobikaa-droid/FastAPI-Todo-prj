from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from datetime import datetime, timezone

from ..database import Base
from ..models.users_models import User


class Todo(Base):
    __tablename__ = "todos"

    pk: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    important: Mapped[bool] = mapped_column(Boolean, default=False)
    creation_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    last_update_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    completed_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    user_pk: Mapped[int | None] = mapped_column(
        ForeignKey("users.pk"),
        nullable=True
    )
    user: Mapped["User"] = relationship("User", backref="todos")
