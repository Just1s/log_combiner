from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User
from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user
from . import my_functions as f

auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nickname = request.form.get('nickname')
        password = request.form.get('password')

        user = User.query.filter_by(nickname=nickname.lower()).first()
        if user:
            if check_password_hash(user.password, password):
                flash('Logged in!', category='success')
                login_user(user, remember=True)
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect password.', category='error')
        else:
            flash('Nickname doesn\'t exist.', category='error')
    return render_template('login.html', user=current_user)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get('email')
        nickname = request.form.get('nickname')
        steamid = request.form.get('steamid')
        api_key = request.form.get('api_key')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        user_email = User.query.filter_by(email=email).first()
        user_nickname = User.query.filter_by(nickname=nickname).first()
        if user_nickname:
            flash('Nickname already taken.', category='error')
        elif user_email:
            flash('Email already taken.', category='error')
        elif len(email) < 4:
            flash('Incorrect email.', category='error')
        elif len(nickname) < 3:
            flash('Nickname must be 3 characters or longer.', category='error')
        elif len(steamid) != 17:
            flash('Incorrent steamID64 format.', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
        elif len(password1) < 4:
            flash('Password must be 4 characters or longer.', category='error')
        else:
            profile_pic, etf2l_id = f.etf2l_data(steamid)
            if len(api_key) < 1:
                api_key = None
            new_user = User(email=email.lower(), nickname=nickname.lower(), api_key=api_key, steamid=steamid,
                            profile_pic=profile_pic, etf2l_id=etf2l_id, password=generate_password_hash(password1, method='sha256'))
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash('Account created!', category='success')
            return redirect(url_for('views.home'))

    return render_template('sign_up.html', user=current_user)
