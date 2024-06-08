from flask import render_template, session, abort, request, Flask
from flask.views import View
import os
import json
import datetime
from shared import load_secrets

class HomePage(View):
    def __init__(self, template, data_folder, app: Flask):
        self.template = template
        self.data_folder = data_folder
        self.app = app

    def dispatch_request(self):
        secrets = load_secrets()

        passkey = request.args.get("access_key")

        if secrets["pass-key"] and (not passkey or passkey != secrets["pass-key"]):
            abort(404)
        else:
            summary_file = os.path.join(self.data_folder, 'workers_summary.json')
            file_path = os.path.join(self.app.static_folder, 'worker_uptime_pie_chart.png')
            if os.path.exists(summary_file):
                with open(summary_file, 'r') as f:
                    summary_data = json.load(f)
            else:
                summary_data = {}
            if os.path.exists(file_path):
                last_modified_time = datetime.datetime.utcfromtimestamp(os.path.getmtime(file_path))
                last_modified_str = last_modified_time.strftime("%Y-%m-%d %H:%M:%S")
            else:
                last_modified_str = None
            return render_template(self.template, summary_data=summary_data, last_updated=last_modified_str)