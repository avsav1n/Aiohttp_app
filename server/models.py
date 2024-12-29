from datetime import datetime

import sqlalchemy as sq
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

import server.config as cfg

DSN = (
    f"postgresql+asyncpg://{cfg.POSTGRES_USER}:"
    f"{cfg.POSTGRES_PASSWORD}@{cfg.POSTGRES_HOST}:"
    f"{cfg.POSTGRES_PORT}/{cfg.POSTGRES_DB}"
)
engine = create_async_engine(url=DSN)
Session = async_sessionmaker(bind=engine, expire_on_commit=False)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    """Модель таблицы 'user'."""

    __tablename__ = "user"

    id: Mapped[int] = mapped_column(sq.Integer, primary_key=True)
    username: Mapped[str] = mapped_column(sq.String(50), unique=True)
    password: Mapped[str] = mapped_column(sq.String(100))
    registered_at: Mapped[datetime] = mapped_column(sq.DateTime, server_default=sq.func.now())

    advertisements: Mapped[list["Advertisement"]] = relationship(
        "Advertisement", back_populates="user", cascade="all, delete-orphan"
    )

    def __str__(self):
        return f"{self.__tablename__}: {self.username}"

    @property
    def as_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "registered_at": self.registered_at.isoformat(),
        }


class Advertisement(Base):
    """Модель таблицы 'advertisement'."""

    __tablename__ = "advertisement"

    id: Mapped[int] = mapped_column(sq.Integer, primary_key=True)
    id_user: Mapped[int] = mapped_column(sq.Integer, sq.ForeignKey(User.id, ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(sq.String(50), nullable=False, unique=True)
    text: Mapped[str] = mapped_column(sq.Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(sq.DateTime, server_default=sq.func.now())
    updated_at: Mapped[datetime] = mapped_column(
        sq.DateTime, server_default=sq.func.now(), onupdate=sq.func.now()
    )

    user: Mapped["User"] = relationship(User, back_populates="advertisements")

    def __str__(self):
        max_len = 15
        return (
            f"{self.__tablename__}: "
            f"{self.title[:max_len] + ('' if len(self.title) < max_len else '...')}"
        )

    @property
    def as_dict(self):
        return {
            "id": self.id,
            "id_user": self.id_user,
            "title": self.title,
            "text": self.text,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


async def close_orm():
    await engine.dispose()


ORM_MODELS = User | Advertisement
