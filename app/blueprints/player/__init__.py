from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.exceptions import NotAuthorizedException
from app.models import PlayerProfile, Roles
from flask_paginate import Pagination, get_page_parameter
from app.forms import PlayerProfileForm, flash_errors
from app.db import db_session

players = Blueprint('players', __name__, template_folder='templates', url_prefix='/players')


@players.route('/')
def list():
    page = request.args.get(get_page_parameter(), type=int, default=1)
    per_page = 20
    query = PlayerProfile.query
    players = query.limit(per_page).offset(per_page * (page - 1)).all()
    pagination = Pagination(
        page=page,
        per_page=per_page,
        total=query.count(),
        record_name='players',
        bs_version=4
    )
    return render_template('players.html', players=players, pagination=pagination, can_edit=can_edit_player())


def can_edit_player():
    if current_user is None:
        return False
    return Roles.ADMIN.value in [user_role.role for user_role in current_user.roles] \
        or Roles.CONTRIBUTOR.value in [user_role.role for user_role in current_user.roles]


@players.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    can_edit = can_edit_player()
    if not can_edit:
        raise NotAuthorizedException
    form = PlayerProfileForm()
    if form.validate_on_submit():
        player = PlayerProfile(
            nick=form.nick.data,
            country_iso=form.country_iso.data
        )
        db_session.add(player)
        db_session.commit()
        flash("player profile added")
        return redirect(url_for('players.list'))
    else:
        flash_errors(form)
    return render_template('player_edit.html', form=form, can_edit=can_edit)


@players.route('/edit/<player_id>', methods=['GET', 'POST'])
def edit(player_id):
    player = PlayerProfile.query.filter(PlayerProfile.id == player_id).one()
    form = PlayerProfileForm(nick=player.nick, country_iso=player.country_iso)
    if form.validate_on_submit():
        player.nick = form.nick.data
        player.country_iso = form.country_iso.data
        db_session.commit()
        flash("player profile updated")
        return redirect(url_for('players.list'))
    return render_template('player_edit.html', form=form)


@players.route('/<player_id>', methods=['GET', 'POST'])
def view(player_id):
    player = PlayerProfile.query.filter(PlayerProfile.id == player_id).one()
    return render_template('view.html', player=player, can_edit=can_edit_player())


@players.route('/<player_id>/delete', methods=['POST'])
@login_required
def delete(player_id):
    if not can_edit_player():
        raise NotAuthorizedException
    PlayerProfile.query.filter(PlayerProfile.id == player_id).delete()
    db_session.commit()
    flash('Player deleted')
    return redirect(url_for('players.list'))

