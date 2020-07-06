from app import create_app, socketio
import config
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from app.db import db_session

try:
    sentry_sdk.init(
        config.SENTRY_DSN,
        integrations=[FlaskIntegration()]
    )
except AttributeError:
    # WITHOUT SENTRY
    pass

app = create_app(debug=True)


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


if __name__ == '__main__':
    socketio.run(app)
