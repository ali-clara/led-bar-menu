from flask import Flask
from services.test_class import TestView

app = Flask(__name__, template_folder="templates")

TestView.register(app, route_base = '/')
app.register_error_handler(404, TestView.not_found)
app.config['TEMPLATES_AUTO_RELOAD'] = True 
app.run(host='0.0.0.0', port=5000, debug=True)