from sqlalchemy import Column, Integer, String
from app.db import Base

target_metadata = Base.metadata


class Render(Base):
    id = Column(Integer, primary_key=True)
    streamable_short = Column(String(8))
    state = Column(String(50))
    title = Column(String(255))
    gtv_match_id = Column(Integer())
    map_number = Column(Integer())
    client_num = Column(Integer())
    start = Column(Integer())
    end = Column(Integer())
