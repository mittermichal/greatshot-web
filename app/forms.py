from flask_wtf import FlaskForm
from wtforms import StringField, FileField, SelectField, HiddenField, validators
from wtforms.fields.html5 import IntegerField
from app.countries import countries


class ExportFileForm(FlaskForm):
    file = FileField('Demo')


class ExportMatchLinkForm(FlaskForm):
    gtv_match_id = StringField('Match link',
                               render_kw={"placeholder": "http://www.gamestv.org/event/56051-tag-vs-elysium/"})
    map_number = IntegerField('Map number', default=1, render_kw={"min": 1})


class CutForm(FlaskForm):
    start = IntegerField('Start', render_kw={"step": 1000}, default=0)
    end = IntegerField('End', render_kw={"step": 1000}, default=2147483000)
    cut_type = SelectField('Cut type', choices=[(0, 'SNAPNUMBER'), (1, 'SNAPTIME'), (2, 'SNAPCOUNT')], default=1)
    client_num = StringField('Client number *', render_kw={"placeholder": "0"})
    gtv_match_id = HiddenField('gtv_match_id')
    map_number = HiddenField('map_number')
    filename = HiddenField('filename')
    filepath = HiddenField('filepath')


class RenderForm(FlaskForm):
    title = StringField('Title')
    crf = IntegerField('crf (default:23)', [validators.NumberRange(min=18, max=25)], default=23)
    name = StringField('Name')
    country = SelectField('Country', choices=[(x, x) for x in [None]+countries], default=None)
