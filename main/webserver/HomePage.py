from flask import render_template, session
from flask.views import View

class HomePage(View):
    def __init__(self, template):
        self.template = template
        
    def dispatch_request(self):
        return render_template(self.template)