import sqlalchemy as sq
from sqlalchemy.ext.asyncio import AsyncSession

from server.exceptions import ConflictError, NotFoundError
from server.models import ORM_MODELS, User
from server.security import hash_password


class DataBase:
    def __init__(self, model: ORM_MODELS, session: AsyncSession):
        self.model: ORM_MODELS = model
        self.session: AsyncSession = session

    async def save_changes(self, obj: ORM_MODELS = None) -> None:
        if obj:
            self.session.add(instance=obj)
        try:
            await self.session.commit()
        except sq.exc.IntegrityError:
            raise ConflictError(f"{self.model.__tablename__.title()}-model object already exists")

    async def get_user_by_name(self, username: str) -> User:
        query = sq.select(User).where(User.username == username)
        user: User = await self.session.scalar(query)
        if user:
            return user
        raise NotFoundError(
            f"{self.model.__tablename__.title()}-model object with {username=} not found"
        )

    async def get_obj(self, id: int) -> ORM_MODELS:
        obj: ORM_MODELS = await self.session.get(entity=self.model, ident=id)
        if obj:
            return obj
        raise NotFoundError(f"{self.model.__tablename__.title()}-model object with {id=} not found")

    async def get_objects(self) -> list[ORM_MODELS]:
        objects: list[ORM_MODELS] = await self.session.scalars(sq.select(self.model))
        return objects

    async def create_obj(self, data: dict) -> ORM_MODELS:
        if data.get("password"):
            data: dict = hash_password(data=data)
        obj: ORM_MODELS = self.model(**data)
        await self.save_changes(obj=obj)
        await self.session.refresh(obj)
        return obj

    async def update_obj(self, obj: ORM_MODELS, data: dict) -> ORM_MODELS:
        if data.get("password"):
            data: dict = hash_password(data=data)
        for attr, value in data.items():
            setattr(obj, attr, value)
        await self.save_changes(obj=obj)
        await self.session.refresh(obj)
        return obj

    async def delete_obj(self, obj: ORM_MODELS) -> ORM_MODELS:
        await self.session.delete(instance=obj)
        await self.save_changes()
