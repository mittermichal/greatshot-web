from sqlalchemy import Column, Integer, String
from app.db import Base

class Render(Base):
    __tablename__ = 'renders'
    id = Column(Integer, primary_key=True)
    celery_id = Column(String(50), unique=True, index=True)
    streamable_short = Column(String(8))

    def __init__(self, celery_id=None):
        self.celery_id = celery_id
        self.streamable_short = None

    def __repr__(self):
        return '<Render %r>' % (self.celery_id)