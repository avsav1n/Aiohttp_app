from typing import NamedTuple

import factory
import sqlalchemy as sq

from server.models import Advertisement, Session, User


class BaseFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        abstract = True
        sqlalchemy_session_factory = Session

    @classmethod
    async def _create(cls, model_class, *args, **kwargs):
        obj = model_class(*args, **kwargs)
        async with cls._meta.sqlalchemy_session_factory() as session:
            session.add(obj)
            try:
                await session.commit()
            except sq.exc.IntegrityError:
                await session.rollback()
                unique_column = cls._meta.sqlalchemy_get_or_create
                query = sq.select(cls._meta.model).where(sq.text(f"{unique_column}=:value"))
                obj = await session.scalar(query, {"value": getattr(obj, unique_column)})
        return obj


class UserFactory(BaseFactory):
    username: str = factory.Faker("hostname")
    password: str = factory.Faker("password")

    class Meta:
        model = User
        sqlalchemy_get_or_create: str = "username"


class AdvertisementFactory(BaseFactory):
    title: str = factory.Faker("sentence", variable_nb_words=False, nb_words=4)
    text: str = factory.Faker("paragraph", nb_sentences=10)

    class Meta:
        model = Advertisement
        sqlalchemy_get_or_create: str = "title"

    @classmethod
    async def _create(cls, model_class, *args, **kwargs):
        if not kwargs.get("user"):
            user: User = await UserFactory.create()
            kwargs.update({"user": user})
        return await super()._create(model_class, *args, **kwargs)


class ClientInfo(NamedTuple):
    id: int
    username: str
    auth_headers: str
    registered_at: str
    model: User
