from flask import Response, flash
from shutil import disk_usage


def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )


def flash_errors(form):
    """Flashes form errors"""
    for field, errors in form.errors.items():
        for error in errors:
            flash(u"Error in the %s field - %s" % (
                getattr(form, field).label.text,
                error
            ), 'error')


def check_disk_space():
    if disk_usage('/')[2]/(2**30) < 0.5:
        raise LowDiskSpaceException


class LowDiskSpaceException(Exception):
    def __str__(self):
        return 'Server disk space is too low'
