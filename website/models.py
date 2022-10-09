from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func


class User(db.Model, UserMixin):
    """ Lentelės modelis vartotojų duomenims saugoti. """
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50), unique=True)
    nickname = db.Column(db.String(50), unique=True)
    steamid = db.Column(db.String(50), unique=True)
    api_key = db.Column(db.String(50), default='565d832560e659e6626131e225a0bc40')
    profile_pic = db.Column(db.String(50))
    etf2l_id = db.Column(db.String(50))
    password = db.Column(db.String(150))
    combine = db.relationship('Combine')


class Combine(db.Model):
    """ Lentelės modelis log failų sujungimo duomenim saugoti. """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    title = db.Column(db.String(50))
    log1 = db.Column(db.String(50))
    log2 = db.Column(db.String(50))
    uploaded_log = db.Column(db.String(50), default=None)
    logs = db.relationship('Logs')


class Logs(db.Model):
    """ Lentelės modelis sujungtiems duomenims saugoti. """
    id = db.Column(db.Integer, primary_key=True)
    combine_id = db.Column(db.Integer, db.ForeignKey('combine.id'))
    index = db.Column(db.String(100))
    team = db.Column(db.String(10))
    p_class = db.Column('class', db.String(20))
    kills = db.Column(db.Integer)
    deaths = db.Column(db.Integer)
    assists = db.Column(db.Integer)
    kapd = db.Column('ka/d', db.Float)
    kpd = db.Column('k/d', db.Float)
    damage = db.Column(db.Integer)
    dt = db.Column('damage taken', db.Integer)
    hr = db.Column('heals recieved', db.Integer)
    ubers = db.Column(db.Integer)
