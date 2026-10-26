from typing import TYPE_CHECKING

from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy.model import Model as FlaskModel
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Flask-SQLAlchemy types ``db.Model`` without SQLAlchemy's keyword constructor,
# so type checkers (Pylance/Pyright) reject calls like ``User(username=...)``.
# For type checking only, describe the model base as what it is at runtime:
# SQLAlchemy's declarative base (keyword ``__init__``) plus Flask-SQLAlchemy's
# Model (``query``). At runtime ``db.Model`` is used unchanged.
if TYPE_CHECKING:
    class BaseModel(Base, FlaskModel):
        __abstract__ = True
else:
    BaseModel = db.Model
