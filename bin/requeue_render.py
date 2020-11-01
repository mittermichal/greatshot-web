#!/usr/bin/env python
# before use SET PYTHONPATH=<project_path>
# TODO: https://flask.palletsprojects.com/en/1.1.x/cli/#custom-scripts
import sys
from app.views.renders import render_cut_filepath
from render_worker import tasks
from flask import url_for
from app import create_app
from app.models import Render

app = create_app(debug=True)

render_id = sys.argv[1]

render = Render.query.filter(Render.id == render_id).one()
print("Queueing this render: ", render)

with app.app_context():
    demo_url = url_for(
        'static',
        filename=render_cut_filepath(
            render.gtv_match_id,
            render.map_number,
            render.client_num,
            render.start,
            render.end
        )
    )

print("Cut demo url:", demo_url)
# exit()


tasks.render.send(
    render.id,
    demo_url,
    render.start, render.end
)
