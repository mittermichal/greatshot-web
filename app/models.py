from sqlalchemy import Table, MetaData, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, backref
from app.db import Base

target_metadata = Base.metadata


class Render(Base):
    __tablename__ = 'renders'
    id = Column(Integer, primary_key=True)
    celery_id = Column(String(50), unique=True, index=True)
    streamable_short = Column(String(8))
    title = Column(String(255))
    gtv_match_id = Column(Integer())
    map_number = Column(Integer())
    client_num = Column(Integer())
    player_id = Column(Integer, ForeignKey('players.id'))

    def __init__(self, celery_id=None, title=None, gtv_match_id=None, map_number=None , client_num=None, player_id=None):
        self.celery_id = celery_id
        self.streamable_short = None
        self.title = title
        self.gtv_match_id = gtv_match_id
        self.map_number = map_number
        self.client_num = client_num
        self.player_id = player_id

    def __repr__(self):
        return '<Render %r>' % (self.celery_id)


demos = Table('match_demos', Base.metadata,
    Column('match_id', Integer, ForeignKey('matches.id'), primary_key=True),
    Column('demo_md5', String, ForeignKey('demo.szMd5'), primary_key=True)
)


class Match(Base):
    __tablename__ = 'matches'
    id = Column(Integer, primary_key=True)
    gamestv_id = Column(Integer, unique=True, index=True)
    title = Column(String(255))
    demos = relationship('demo', secondary=demos, lazy='subquery',
       backref=backref('matches', lazy=True))


    def __init__(self, gamestv_id=None, title=None):
        self.gamestv_id = gamestv_id
        self.title = title


class Demo(Base):
    __tablename__ = 'demo'
    id = Column(Integer, primary_key=True)
    szMd5 = Column(Integer, unique=True, index=True)


class Player(Base):
    __tablename__ = 'players'
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    country = Column(String(5))
    # def __init__(self, name=None, country=None):
    #    self.name = name
    #    self.country = country

class MatchPlayer(Base):
    __tablename__ = 'demo_players'
    id = Column(Integer, primary_key=True)
    demo_id = Column(Integer())
    client_num = Column(Integer())
    player_id = Column(Integer, ForeignKey('players.id'))



