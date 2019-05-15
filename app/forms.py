from wtforms import StringField, FileField, SelectField, HiddenField, validators, BooleanField
from wtforms.fields.html5 import IntegerField, IntegerRangeField
from flask_wtf import Form
from app.countries import countries

class ExportFileForm(Form):
    file = FileField('Demo')

class ExportMatchLinkForm(Form):
    gtv_match_id = StringField('Match link', render_kw={"placeholder": "http://www.gamestv.org/event/56051-tag-vs-elysium/"})
    map_number = StringField('Map number', render_kw={"placeholder": "1"})

class CutForm(Form):
    start = IntegerField('Start', render_kw={"step":1000}, default=0)
    end = IntegerField('End', render_kw={"step":1000},default=2147483000)
    cut_type = SelectField('Cut type', choices=[(0, 'SNAPNUMBER'), (1, 'SNAPTIME'), (2, 'SNAPCOUNT')], default=1)
    client_num = StringField('Client number<sup>*</sup>', render_kw={"placeholder": "0"})
    gtv_match_id = HiddenField('gtv_match_id')
    map_number = HiddenField('map_number')
    filename = HiddenField('filename')


class RenderForm(Form):
    title = StringField('Title')
    crf = IntegerField('crf (default:23)', [validators.NumberRange(min=18, max=25)], default=23)
    name = StringField('Name')
    country = SelectField('Country', choices=[(x, x) for x in countries], default='eu')
    download = BooleanField('Download', default=False)
    streamable = BooleanField('Streamable', default=True)

class PlayerForm(Form):
    name = StringField('Name')
    country = SelectField('Country', choices=[(x,x) for x in countries], default='eu')
    #gtv_mame = SelectField('gtv_mame')
    client_num = HiddenField('client_num')
