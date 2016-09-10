from app.db import init_db, db_session
from app.models import Render
init_db()

def delete_renders():
  for r in Render.query.all():
    db_session.delete(r)