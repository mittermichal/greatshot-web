from flask_wtf import FlaskForm
from wtforms import StringField, FileField, SelectField, HiddenField, PasswordField, BooleanField, SubmitField, SelectMultipleField, validators
from wtforms.validators import ValidationError, DataRequired, EqualTo
from wtforms.fields.html5 import IntegerField
from app.countries import countries
from app.models import User, Roles
from flask import flash


class ExportFileForm(FlaskForm):
    file = FileField('Demo')


class ExportMatchLinkForm(FlaskForm):
    gtv_match_id = StringField('Match link',
                               render_kw={"placeholder": "http://www.gamestv.org/event/56051-tag-vs-elysium/"})
    map_number = IntegerField('Map number', [validators.NumberRange(min=1)], default=1, render_kw={"min": 1})


class CutForm(FlaskForm):
    start = IntegerField('Start', default=0)
    end = IntegerField('End', default=2147483000)
    length = StringField('Length', render_kw={"disabled": "disabled"})
    cut_type = SelectField('Cut type', choices=[
            ('0', 'SNAPNUMBER'),
            ('1', 'SNAPTIME'),
            ('2', 'SNAPCOUNT')
        ], default='1')
    client_num = StringField('Client number *', render_kw={"placeholder": "0"})
    gtv_match_id = HiddenField('gtv_match_id')
    map_number = HiddenField('map_number')
    filename = HiddenField('filename')
    filepath = HiddenField('filepath')

    def validate_render_length(self):
        length = self.end.data - self.start.data
        if length > 1000*30 or length < 4000:
            self.length.errors.append("Length of render has to be between 4000 and 30000 miliseconds")
            return False
        else:
            return True


class RenderForm(FlaskForm):
    title = StringField('Title')
    crf = IntegerField(
        'encode quality **',
        [validators.NumberRange(min=18, max=51)],
        default=23,
        render_kw={"min": 18, "max": 51}
    )
    name = StringField('Name')
    country = SelectField('Country', choices=[(x, x) for x in ["None"]+countries], default="None")


class LoginForm(FlaskForm):
    nick = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    nick = StringField('Nick', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_nick(self, nick):
        # Render.query.filter(Render.id == render_id).one()
        user = User.query.filter(User.nick == nick.data).first()
        if user is not None:
            raise ValidationError('Nick "{}" already taken'.format(nick.data))


class UserForm(FlaskForm):
    roles = SelectMultipleField(
        'roles',
        choices=[(str(role.value), role.name) for role in Roles],
        render_kw={"autocomplete": "Off"}
    )
    submit = SubmitField('Save')


class PlayerProfileForm(FlaskForm):
    nick = StringField('Nick', validators=[DataRequired()])
    country_iso = SelectField('Country', choices=[(x, x) for x in countries])
    submit = SubmitField('Save')


class PlayerDemoForm(FlaskForm):
    player_id = SelectField('Nick')
    country_iso = SelectField('Country', choices=[(x, x) for x in countries])
    submit = SubmitField('Save')


def flash_errors(form):
    """Flashes form errors"""
    for field, errors in form.errors.items():
        for error in errors:
            flash(u"Error in the %s field - %s" % (
                getattr(form, field).label.text,
                error
            ), 'error')