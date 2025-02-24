from app import create_app, init_config, config_path

import os

init_config()
app = create_app()
if not os.path.exists(app.config['PARSERPATH']):
    raise Exception(
        f"{app.config['PARSERPATH']} not found\n"
        f"download {app.config['PARSERPATH']} or edit PARSERPATH in {config_path}"
    )

if __name__ == '__main__':
    app.run()
