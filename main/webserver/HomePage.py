from flask import render_template, session, abort, request
from flask.views import View
import os
import json
from shared import load_secrets

class HomePage(View):
    def __init__(self, template, data_folder):
        self.template = template
        self.data_folder = data_folder
        
    def dispatch_request(self):
        secrets = load_secrets()

        passkey = request.args.get("access_key")

        if secrets["pass-key"] and (not passkey or passkey != secrets["pass-key"]):
            abort(404)
        else:
            summary_file = os.path.join(self.data_folder, 'workers_summary.json')
        
            if os.path.exists(summary_file):
                with open(summary_file, 'r') as f:
                    summary_data = json.load(f)
            else:
                summary_data = {}
        
            return render_template(self.template, summary_data=summary_data)