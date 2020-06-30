from sqlalchemy import Column, Integer, String, SmallInteger, ForeignKey
from sqlalchemy.orm import relationship
from app.db import Base
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from enum import IntEnum
from app.Libtech3 import Player

# target_metadata = Base.metadata


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


class UserRoles(Base):
    __tablename__ = 'user_roles'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    role = Column(SmallInteger)

    def __repr__(self):
        return str(Roles(self.role))


class User(UserMixin, Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    nick = Column(String(50), unique=True)
    password_hash = Column(String(128))
    roles = relationship("UserRoles")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Roles(IntEnum):
    ADMIN = 1
    CONTRIBUTOR = 2


class PlayerProfile(Base):
    __tablename__ = 'player_profiles'
    id = Column(Integer, primary_key=True)
    nick = Column(String(8))
    country_iso = Column(String(8))
    demos = relationship("PlayerDemo")
    # demo_player = relationship("player")


class PlayerDemo(Base):
    __tablename__ = 'player_demos'
    player_profile_id = Column(Integer, ForeignKey('player_profiles.id'), primary_key=True)
    demo_player_id = Column(Integer, ForeignKey(Player.dwSeq), primary_key=True)
