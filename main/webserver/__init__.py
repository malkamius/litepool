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

def run():

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

    # @app.route('/worker_uptime_pie_chart.png')
    # def uptime_chart():
    #     return send_from_directory(app.static_folder, 'worker_uptime_pie_chart.png')

    app.run(host=secrets["http_listen_on"], port=secrets["http_port"])
    

