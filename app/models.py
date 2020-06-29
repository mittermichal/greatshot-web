from sqlalchemy import Column, Integer, String, SmallInteger
from app.db import Base
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

target_metadata = Base.metadata


class Render(Base):
    __tablename__ = 'renders'
    id = Column(Integer, primary_key=True)
    streamable_short = Column(String(8))
    status_msg = Column(String(50))
    progress = Column(SmallInteger())
    title = Column(String(255))
    gtv_match_id = Column(Integer())
    map_number = Column(Integer())
    client_num = Column(Integer())
    start = Column(Integer())
    end = Column(Integer())

    def __repr__(self):
        return str(vars(self)).replace(',', ',\n')


class User(UserMixin, Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    nick = Column(String(50), unique=True)
    password_hash = Column(String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
