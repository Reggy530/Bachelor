from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint, and_
from datetime import datetime, timedelta
import requests
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
app.config['SECRET_KEY'] = 'borjar'
db = SQLAlchemy()
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
default_cashflow_entries = [['Allegro', 'Borjar'],['Faglar', 'Hunja']]

# Create a user_loader callback
@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)

#Create admin-only decorator
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        #If id is not 1 then return abort with 403 error
        if current_user.id != 1:
            return abort(403)
        #Otherwise continue with the route function
        return f(*args, **kwargs)
    return decorated_function



class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))
    current_period = db.Column(db.Integer, default=4)

class Assets(db.Model):
    __tablename__ = 'assets'
    asset_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    period = db.Column(db.Integer)
    name = db.Column(db.String(100))
    value_pcs = db.Column(db.Float)
    amount = db.Column(db.Float)
    value_pln = db.Column(db.Float)
    __table_args__ = (
        UniqueConstraint('name', 'period', 'user_id', name='_name_period_uc'),
    )

class Budget(db.Model):
    __tablename__ = 'budget'
    budget_id = db.Column(db.Integer, primary_key=True)
    is_income = db.Column(db.Integer)
    user_id = db.Column(db.Integer)
    period = db.Column(db.Integer)
    name = db.Column(db.String(100))
    amount = db.Column(db.Float)
    estimated = db.Column(db.Float)
    __table_args__ = (
        UniqueConstraint('name', 'period', 'user_id', name='unique_budget'),
    )

with app.app_context():
    db.create_all()

# Przykładowe dane - kategorie budżetu i zarobków
budget_data = {
    'dom': 1500,
    'samochód': 500,
    'jedzenie': 800,
    # Dodaj więcej kategorii budżetu
}

earnings_data = {
    'pensja': 3000,
    'inwestycje': 1000,
    # Dodaj więcej kategorii zarobków
}

@app.route('/', methods=["GET", "POST"])
def main():

    print(current_user)
    return render_template('index.html', user=current_user, current_page='index.html')

@app.route('/current_month', methods=['GET'])
def current_month():
    # Pobierz bieżący miesiąc dla aktualnego użytkownika z bazy danych
    current_month = current_user.current_period
    return str(current_month)

@app.route('/cashflow', methods=["GET", "POST"])
def cashflow():
    if request.method == "POST":
        data = request.get_json()
        db.session.query(Assets).filter_by(user_id=current_user.id, period=current_user.current_period).delete()
        for dd in data:
            asset = Assets(
                user_id = current_user.id,
                period = current_user.current_period,
                name = dd['name'],
                value_pcs= float(dd['value_pcs']) if dd['value_pcs'] else 1,
                amount = float(dd['amount']) if dd['amount'] else None,
                value_pln = float(dd['value_pln']) if dd['value_pln'] else None

            )
            print(asset)
            db.session.add(asset)
        db.session.commit()

    result = db.session.execute(
        db.select(Assets).where(and_(Assets.user_id == current_user.id, Assets.period == current_user.current_period)))

    data = result.fetchall()
    print(data)

    return render_template('cashflow.html', user=current_user, current_page='cashflow.html', values=default_cashflow_entries, data=data)

@app.route('/update_month', methods=['POST'])
def update_month():
    selected_month = request.form['month']

    # Przekształć datę w formacie "YYYY-MM" na numer miesiąca
    year, month = map(int, selected_month.split('-'))
    month_number = (year - 2024) * 12 + month

    print("Numer miesiąca:", month_number)  # Sprawdzamy numer miesiąca w konsoli

    # Aktualizuj wartość current_period dla aktualnego użytkownika
    current_user.current_period = month_number
    db.session.commit()
    return 'OK'

@app.route('/budget', methods=['GET', 'POST'])
def budget():
    if request.method == "POST":
        data = request.get_json()
        print(data)
        db.session.query(Budget).filter_by(user_id=current_user.id, period=current_user.current_period).delete()
        for dd in data:
            budgett = Budget(
                user_id=current_user.id,
                period=current_user.current_period,
                name=dd['name'],
                is_income=dd['is_income'],
                estimated=float(dd['estimated']) if dd['estimated'] else None,
                amount=float(dd['amount']) if dd['amount'] else None
            )
            print("zmienna budgett ", budgett)
            db.session.add(budgett)

        db.session.commit()
        print('test')

    result = db.session.execute(
        db.select(Budget).where(and_(Budget.user_id == current_user.id, Budget.period == current_user.current_period)))

    data = result.fetchall()
    print(data)

    return render_template('budget.html', user=current_user, current_page='budget.html', data=data)

@app.route('/stats')
def stats():
    return render_template('stats.html', user=current_user, current_page='stats.html')

@app.route('/loans')
def loans():
    return render_template('loans.html', user=current_user, current_page='loans.html')

@app.route('/profile')
def profile():
    return render_template('profile.html', user=current_user, current_page='profile.html')

@app.route('/admin_settings')
@admin_only
def admin_settings():
    return render_template('admin_settings.html', user=current_user, current_page='admin_settings.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main'))

@app.route('/login_page',methods=["GET", "POST"])
def login_page():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')
        result = db.session.execute(db.select(User).where(User.email == email))
        user = result.scalar()
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login_page'))
        else:
            login_user(user)
            return redirect(url_for('main'))

    return render_template('login_page.html', user=current_user, current_page='login_page.html')

@app.route('/register',methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get('email')
        result = db.session.execute(db.select(User).where(User.email == email))
        user = result.scalar()
        if user:
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login_page'))
        hash_and_salted_password = generate_password_hash(
            request.form.get('password'),
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            email=request.form.get('email'),
            password=hash_and_salted_password,
            name=request.form.get('name'),
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("main"))
    # Passing True or False if the user is authenticated.
    return render_template("register.html", user=current_user)


if __name__ == "__main__":
    app.run(debug=True, port=2137)

