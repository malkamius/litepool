import pandas as pd
from flask import Flask, send_from_directory, request
import logging as baselogging
from shared.mylogging import logging
import os
import sys
from .HomePage import HomePage
import signal
import json

from shared import load_secrets

def _windows_enable_ANSI(std_id):
    """Enable Windows 10 cmd.exe ANSI VT Virtual Terminal Processing."""
    from ctypes import byref, POINTER, windll, WINFUNCTYPE
    from ctypes.wintypes import BOOL, DWORD, HANDLE

    GetStdHandle = WINFUNCTYPE(
        HANDLE,
        DWORD)(('GetStdHandle', windll.kernel32))

    GetFileType = WINFUNCTYPE(
        DWORD,
        HANDLE)(('GetFileType', windll.kernel32))

    GetConsoleMode = WINFUNCTYPE(
        BOOL,
        HANDLE,
        POINTER(DWORD))(('GetConsoleMode', windll.kernel32))

    SetConsoleMode = WINFUNCTYPE(
        BOOL,
        HANDLE,
        DWORD)(('SetConsoleMode', windll.kernel32))

    if std_id == 1:       # stdout
        h = GetStdHandle(-11)
    elif std_id == 2:     # stderr
        h = GetStdHandle(-12)
    else:
        return False

    if h is None or h == HANDLE(-1):
        return False

    FILE_TYPE_CHAR = 0x0002
    if (GetFileType(h) & 3) != FILE_TYPE_CHAR:
        return False

    mode = DWORD()
    if not GetConsoleMode(h, byref(mode)):
        return False

    ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
    if (mode.value & ENABLE_VIRTUAL_TERMINAL_PROCESSING) == 0:
        SetConsoleMode(h, mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING)
    return True
app = Flask(__name__)
app.static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')

logger = logging.get_logger(loglevel=baselogging.DEBUG, loggername=__name__)

# Define the data and secrets folder paths
app_path = os.path.dirname(os.path.abspath(__file__))
data_folder = os.path.join(app_path, '..', 'data')
secrets_folder = os.path.join(app_path, '..', 'secrets')

secrets_file = os.path.join(secrets_folder, 'secrets.json')
secrets = load_secrets()
home_page = HomePage.as_view("Home", "index.html", data_folder=data_folder, app=app)

routes = {
    '/': {'handler': home_page, 'methods': ['GET']},
    '/Index': {'handler': home_page, 'methods': ['GET']},
}

# Register the routes with Flask
for path, route_info in routes.items():
    app.add_url_rule(path, view_func=route_info['handler'], endpoint=path, methods=route_info['methods'])


@app.route('/shutdown', methods=['POST'])
def shutdown():
    if request.method == 'POST':
        shutdown_server()
        
        return 'Server shutting down...'

def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        logger.error('Not running with the Werkzeug Server')
    else:
        func()
        
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(app.static_folder, 'favicon.ico')

def run():
    try:
        _windows_enable_ANSI(1)
        _windows_enable_ANSI(2)
    except Exception:
        print("Failed to enable ANSI")
    app.run(host=secrets["http_listen_on"], port=secrets["http_port"])
# @app.route('/worker_uptime_pie_chart.png')
# def uptime_chart():
#     return send_from_directory(app.static_folder, 'worker_uptime_pie_chart.png')
if __name__ == "__main__":
    run()

