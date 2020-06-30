from flask import Blueprint, render_template, request
from app.Libtech3 import Demo, Player
from flask_paginate import Pagination, get_page_parameter
from sqlalchemy.orm import contains_eager

libtech3 = Blueprint('libtech3', __name__, template_folder='templates', url_prefix='/libtech3')


@libtech3.route('/demos')
def demo_list():
    page = request.args.get(get_page_parameter(), type=int, default=1)
    per_page = 20
    query = Demo.query
    demos = query.limit(per_page).offset(per_page * (page - 1)).all()
    pagination = Pagination(
        page=page,
        per_page=per_page,
        total=query.count(),
        record_name='demos',
        bs_version=4
    )
    return render_template('demos.html', demos=demos, pagination=pagination)


@libtech3.route('/demo/<demo_id>')
def demo(demo_id):
    demo = Demo.query.join(Demo.players).filter(Player.bTeam <= 2)\
        .filter(Demo.dwSeq == demo_id).options(contains_eager(Demo.players)).one()
    return render_template('demo.html', demo=demo)
