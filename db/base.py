from sqlalchemy import inspect

from db.session import Base, engine
from models import category, transaction, user

def init_db():
    if "expenses" in inspect(engine).get_table_names():
        raise RuntimeError("Run `alembic upgrade head` to migrate expenses to transactions before startup")
    Base.metadata.create_all(bind=engine)
