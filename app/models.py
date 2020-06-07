from sqlalchemy import Column, Integer, String, SmallInteger
from app.db import Base

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
