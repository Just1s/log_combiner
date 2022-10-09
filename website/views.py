import json
import os
import pandas as pd
import requests
from flask import Blueprint, render_template, request, flash, redirect, url_for, Markup
from flask_login import login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from . import my_functions as f
from . import db
from .models import Combine, Logs
from .forms import EditProfileForm, UploadLogForm

views = Blueprint('views', __name__)


@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    """ Funkcija sujungia diejų mačų statistikas į vieną bendrą ir išsaugo duombazėje. """
    if request.method == 'POST':
        logs = [request.form.get('log1'), request.form.get('log2')]
        title = request.form.get('title')
        links_ok, stats = f.check_links(logs)
        if links_ok:
            players_stats1 = stats[0]['players']
            players_stats2 = stats[1]['players']
            player_names = {**stats[0]['names'], **stats[1]['names']}
            combined_stats = f.combine_stats(players_stats1, players_stats2)
            combined_stats = f.remove_keys(combined_stats)

            new_combine = Combine(user_id=current_user.id, log1=logs[0], log2=logs[1], title=title)
            db.session.add(new_combine)
            db.session.commit()

            df = f.make_df(combined_stats, player_names)
            df['combine_id'] = new_combine.id
            df.columns = ['Team', 'Class', 'Kills', 'Deaths', 'Assists', 'KA/D', 'K/D',
                          'Damage', 'Damage Taken', 'Heals Recieved', 'Ubers', 'combine_id']
            df.to_sql('logs', db.engine, if_exists='append')
            df.drop('combine_id', axis=1, inplace=True)

            return redirect(url_for('views.combined_log', combine_id=new_combine.id))

        else:
            flash('One or more links were incorrect', category='error')
            return render_template('home.html', user=current_user)

    return render_template('home.html', user=current_user)


@views.route('/combined_log/<combine_id>')
@login_required
def combined_log(combine_id):
    """ Funkcija atvaizduoti pasirinktą mačų statistiką. """
    combine = Combine.query.get(combine_id)
    if combine.user_id != current_user.id:
        return redirect(url_for('views.home'))
    df = pd.read_sql(f'SELECT * FROM logs WHERE combine_id={combine_id}', db.engine)
    df.drop(['id', 'combine_id'], axis=1, inplace=True)
    df.index += 1
    df.columns = ['Player', 'Team', 'Class', 'Kills', 'Deaths', 'Assists', 'KA/D', 'K/D',
                  'Damage', 'Damage Taken', 'Heals Recieved', 'Ubers']

    return render_template('combined_log.html',
                           tables=[df.to_html(justify="center",
                                              classes='table table-dark table-striped text-center styled-table')],
                           user=current_user, combine_id=combine_id, combine=combine)


@views.route('/combined_logs')
@login_required
def combined_logs():
    """ Funkcija atvaizduoti sąrašą visų vartotojo sujungtų statistikų. """
    return render_template('combined_logs.html', user=current_user)


@views.route('/combined_log/delete/<combine_id>', methods=['GET', 'POST'])
@login_required
def delete_combine(combine_id):
    """ Funkcija ištrinti pasirinktą mačų statistiką. """
    combine = Combine.query.get(combine_id)
    if combine.user_id != current_user.id:
        flash('Combined log deleted.', category='success')
        return redirect(url_for('views.home'))
    if request.method == 'POST':
        if combine.uploaded_log:
            path = './website/log_files/'
            log_id = f.get_logs_ids([combine.log1])
            log_file = f'{log_id[0]}.log'
            full_path = os.path.join(path, log_file)
            os.remove(full_path)

        Logs.query.filter_by(combine_id=combine_id).delete()
        db.session.commit()
        combine = Combine.query.get(combine_id)
        db.session.delete(combine)
        db.session.commit()

        flash('Combined log deleted.', category='success')
        return redirect(url_for('views.combined_logs'))

    return render_template('delete_combine.html', combine=combine, user=current_user)


@views.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """ Funkcija keisti vartotojo duomenims. """
    form = EditProfileForm(obj=current_user)
    if form.validate_on_submit():
        if check_password_hash(current_user.password, form.password.data):
            if form.password1.data == form.password2.data:
                current_user.email = form.email.data
                current_user.nickname = form.nickname.data
                current_user.api_key = form.api_key.data
                if current_user.steamid != form.steamid.data:
                    profile_pic, etf2l_id = f.etf2l_data(form.steamid.data)
                    current_user.profile_pic = profile_pic
                    current_user.etf2l_id = etf2l_id
                    current_user.steamid = form.steamid.data
                if len(form.password1.data) == 0:
                    db.session.commit()
                    flash('Profile info updated.', category='success')
                    return redirect(url_for('views.profile', form=form, user=current_user))
                elif len(form.password1.data) < 4:
                    flash('New password needs to be greater than 3 characters', category='error')
                else:
                    current_user.password = generate_password_hash(form.password1.data, method='sha256')
                    db.session.commit()
                    flash('Profile info updated.', category='success')
                    return redirect(url_for('views.profile', form=form, user=current_user))
            else:
                flash('New passwords don\'t match.', category='error')
        else:
            flash('Incorrect password.', category='error')

    return render_template('profile.html', form=form, user=current_user)


@views.route('/upload/<combine_id>', methods=['GET', 'POST'])
@login_required
def upload(combine_id):
    """ Funkcija sujungtai mačų statistikai įkelti į Logs.tf puslapį. """
    combine = Combine.query.get(combine_id)
    if combine.user_id != current_user.id:
        return redirect(url_for('views.home'))

    logs = [combine.log1, combine.log2]
    logs_ids = f.get_logs_ids(logs)

    form = UploadLogForm()

    if request.method == 'GET':
        form.title.data = combine.title
        form.api_key.data = current_user.api_key

    if form.validate_on_submit():
        files_combined = f.combine_logs_files(logs_ids)
        if files_combined:
            path = './website/log_files/'
            log_file = f'{logs_ids[0]}.log'
            full_path = os.path.join(path, log_file)

            files = {'logfile': open(full_path, 'rb')}
            params = {
                'title': form.title.data,
                'map': form.maps.data,
                'key': form.api_key.data,
                'uploader': 'combiner project'
            }
            r = requests.post('http://logs.tf/upload', files=files, params=params)
            info = json.loads(r.text)
            if info['success']:
                combine.uploaded_log = f'http://logs.tf/{info["log_id"]}'
                db.session.commit()
                flash(Markup(f'''Upload successful. Uploaded log: <a href="http://logs.tf/{info['log_id']}">http://logs.tf/{info['log_id']}</a>'''), category='success')
                return redirect(url_for('views.combined_logs', user=current_user))
            else:
                flash(f'Upload failed. Error: {info["error"]}', category='error')

        else:
            flash('Couldn\'t upload, Logs.tf might be down', category='error')
            return redirect(url_for('views.combined_logs', user=current_user))

    return render_template('upload_log.html', form=form, combine=combine, user=current_user)
