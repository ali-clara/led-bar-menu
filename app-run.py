from flask import Flask, render_template, redirect, url_for
from flask_classful import FlaskView, method, route, request

from services.test_class import TestView

app = Flask(__name__, template_folder="templates")

TestView.register(app, route_base = '/')
app.run(host='0.0.0.0', port=5000, debug=True)