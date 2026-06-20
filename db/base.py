from db.session import Base, engine
from models import user, expense, category

def init_db():
    Base.metadata.create_all(bind=engine)
