from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import requests
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
app.config['SECRET_KEY'] = 'borjar'
db = SQLAlchemy()
db.init_app(app)

# login_manager = LoginManager()
# login_manager.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/', methods=["GET", "POST"])
def main():
    return render_template('index.html')


if __name__ == "__main__":
    app.run(debug=True, port=2137)
