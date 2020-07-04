from flask import Response, flash
import os
import tasks_config
import urllib.request
from urllib.error import HTTPError
import app.gamestv
import requests


def check_auth(username, password):
    return username == tasks_config.STREAMABLE_NAME and password == tasks_config.STREAMABLE_PW


def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )


def get_gtv_demo(gtv_match_id, map_num):
    filename = str(gtv_match_id) + '_' + str(map_num) + '.tv_84'
    if not os.path.exists('upload/'+filename):
        try:
            demo_id = app.gamestv.getMatchDemosId(int(gtv_match_id))
        except HTTPError:
            error_message = "Match not found"
            raise Exception(error_message)
        except IndexError:
            try:
                demo_links = app.gamestv.getDemosDownloadLinks(gtv_match_id)[int(map_num)]
            except IndexError:
                error_message = "Match not available for replay"
                raise Exception(error_message)
        else:
            try:
                demo_links = app.gamestv.getDemosLinks(demo_id)[int(map_num)]
            except IndexError:
                error_message = "demo not found"
                raise Exception(error_message)
            except HTTPError:
                error_message = "no demos for this match"
                raise Exception(error_message)
            except TypeError:
                error_message = "demos are probably private but possible to download"
                raise Exception(error_message)
        try:
            urllib.request.urlretrieve(demo_links, 'upload/' + filename)
        except urllib.error.HTTPError:
            raise Exception("Download from gamestv.org failed - 404")
    return filename


def flash_errors(form):
    """Flashes form errors"""
    for field, errors in form.errors.items():
        for error in errors:
            flash(u"Error in the %s field - %s" % (
                getattr(form, field).label.text,
                error
            ), 'error')
