from .flask_app import app
import logging

if __name__ == "__main__":
    from shared import load_secrets
    secrets = load_secrets()

    try:
        from waitress import serve
        logging.basicConfig(level=logging.DEBUG)
        serve(app, host=secrets["http_listen_on"], port=secrets["http_port"], _quiet = False)
    except ImportError:
        print("Module 'waitress' is not available.")