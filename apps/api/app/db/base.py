from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    __abstract__ = True


from apps.api.app.db import models as models  # noqa: E402,F401
