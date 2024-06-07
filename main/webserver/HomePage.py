from flask import render_template, session
from flask.views import View
import os
import json

class HomePage(View):
    def __init__(self, template, data_folder):
        self.template = template
        self.data_folder = data_folder
        
    def dispatch_request(self):
        summary_file = os.path.join(self.data_folder, 'workers_summary.json')
        
        if os.path.exists(summary_file):
            with open(summary_file, 'r') as f:
                summary_data = json.load(f)
        else:
            summary_data = {}
        
        return render_template(self.template, summary_data=summary_data)