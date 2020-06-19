cmd /k "cd /d venv\Scripts & activate & cd /d ..\.. & dramatiq -t 1 -p 1 tasks app.render_heartbeat -Q render"
