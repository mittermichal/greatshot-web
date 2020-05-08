::python tasks.py worker --concurrency=1 -l info
cmd /k "cd /d venv\Scripts & activate & cd /d ..\.. & celery -A tasks worker --concurrency=1 -l info"
