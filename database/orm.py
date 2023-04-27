from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models import Base, User

from settings.get_token import load_env


engine = create_engine(load_env("URL_POSTGRES"), echo=True)
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)

def add_user(tg_id):
    session = Session()
    user = session.query(User).filter(User.tg_id == tg_id).first()
    if not user:
        new_user = User(tg_id=tg_id)
        session.add(new_user)
        session.commit()

def set_user_city(tg_id, city):
    session = Session()
    user = session.query(User).filter(User.tg_id == tg_id).first()
    if not user.city:
        user.city = city
        session.commit()
