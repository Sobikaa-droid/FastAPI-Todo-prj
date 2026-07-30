from sqlalchemy import String, Boolean, LargeBinary
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from ..database import Base


class User(Base):
    __tablename__ = "users"

    pk: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(32), unique=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[bytes] = mapped_column(LargeBinary)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
