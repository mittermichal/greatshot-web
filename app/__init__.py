from flask import Flask, config
from flask_socketio import SocketIO

app_config = config.Config('.')
app_config.from_pyfile('config.cfg')
socketio = SocketIO(async_mode="eventlet", engineio_logger=True, cors_allowed_origins=app_config['APPHOST'])


def create_app(debug=False):
    """Create an application."""
    app = Flask(__name__)
    app.config.from_pyfile('../config.cfg')
    from app.views.renders import renders
    app.register_blueprint(renders)

    from app.views.main import flask_app as main_blueprint
    app.register_blueprint(main_blueprint)

    socketio.init_app(app, cookie=None)
    return app

# flask_app = Flask(__name__)
# flask_app.config.from_pyfile('config.cfg')
# flask_app.register_blueprint(renders)
# socketio = SocketIO(flask_app, cookie=None)

