import os
import secrets
from flask import Flask

config_path = 'config.cfg'


def create_app():
    """Create an application."""
    app = Flask(__name__)
    app.config.from_pyfile(f'../{config_path}')
    if 'INDEXER' not in app.config:
        if os.name == 'nt':  # windows
            app.config['INDEXER'] = r'indexTarget/app\upload\%s/exportJsonFile/app\download\exports\%s.txt/exportBulletEvents/1/exportDemo/1/exportChatMessages/1/exportRevives/1'
        else:
            app.config['INDEXER'] = r'indexTarget\\app/upload/%s\\exportJsonFile\\app/download/exports/%s.txt\\exportBulletEvents\\1\\exportDemo\\1\\exportChatMessages\\1\\exportRevives\\1'
    from app.views.main import flask_app as main_blueprint
    app.register_blueprint(main_blueprint)
    return app


def init_config():
    if not os.path.exists(config_path):
        print(f'{config_path} not found, creating one with default values')
        if os.name == 'nt':  # windows
            parser_path = 'Anders.Gaming.LibTech3.exe'
        else:
            parser_path = 'LibTech3-linux-x86-64'
        with open(config_path, 'w') as f:
            f.write(
                f"SECRET_KEY='{secrets.token_hex()}'\n"
                f"PARSERPATH='{parser_path}'\n"
                f"MAX_CONTENT_LENGTH = 50 * 1024 * 1024"
                f"DEBUG=True  # set to false for production"
            )
