import flask
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
app = Flask(__name__)

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"