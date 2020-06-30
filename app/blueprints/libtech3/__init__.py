from flask import Blueprint, render_template, request, flash
from sqlalchemy.orm.exc import NoResultFound
from app.Libtech3 import Demo, Player
from flask_paginate import Pagination, get_page_parameter
from sqlalchemy.orm import contains_eager
from app.blueprints.player import can_edit_player
from app.exceptions import NotAuthorizedException
from app.forms import PlayerDemoForm, flash_errors
from app.models import PlayerProfile, PlayerDemo
from app.db import db_session

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


@libtech3.route('/demo/<demo_id>', methods=['GET', 'POST'])
def demo(demo_id):
    demo = Demo.query.join(Demo.players).filter(Player.bTeam <= 2)\
        .filter(Demo.dwSeq == demo_id).options(contains_eager(Demo.players)).one()
    form = PlayerDemoForm()
    players = PlayerProfile.query.all()
    form.player_id.choices = [(str(player.id), player.nick) for player in players]
    if form.validate_on_submit():
        if not can_edit_player():
            raise NotAuthorizedException
        player = PlayerProfile.query.filter(PlayerProfile.id == form.player_id.data).one()
        player.demos.append(PlayerDemo(
            player_profile_id=form.player_id.data,
            demo_player_id=demo_id,
            client_num=form.client_num.data
        ))
        db_session.commit()
        flash("added")
    else:
        flash_errors(form)
    return render_template('demo.html', demo=demo, can_edit_player=can_edit_player(), form=form)
