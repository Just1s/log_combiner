from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, EmailField
from wtforms.validators import Optional, Length, InputRequired


class EditProfileForm(FlaskForm):
    """ Vartotojo duomenų keitimo formos modelis. """
    email = EmailField('Email', validators=[Optional(), Length(min=4, max=50)])
    nickname = StringField('Nickname', validators=[Optional(), Length(min=3, max=50)])
    api_key = StringField('Logs.tf API key', validators=[Optional(), Length(min=4, max=50)])
    steamid = StringField('SteamID64', validators=[Optional(), Length(min=17, max=17)])
    password = PasswordField('Current password', validators=[InputRequired(), Length(min=4, max=50)])
    password1 = PasswordField('New password', validators=[Optional(), Length(max=50)])
    password2 = PasswordField('Confirm new password', validators=[Optional(), Length(max=50)])
    submit = SubmitField('Update')


class UploadLogForm(FlaskForm):
    """ Mačų statistikos įkėlimo į Logs.tf puslapį formos modelis. """
    title = StringField('Title', validators=[InputRequired(), Length(min=1, max=40)])
    maps = StringField('Maps(optional)', validators=[Optional(), Length(max=24)])
    api_key = StringField('Logs.tf API key', validators=[InputRequired(), Length(min=4, max=50)])
    submit = SubmitField('Upload')
