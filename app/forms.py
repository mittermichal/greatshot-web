from wtforms import StringField, FileField, SelectField, HiddenField
from flask_wtf import Form

class ExportFileForm(Form):
    file = FileField('Demo')

class ExportMatchLinkForm(Form):
    matchId = StringField('Match link', render_kw={"placeholder": "http://www.gamestv.org/event/56051-tag-vs-elysium/"})
    map = StringField('Map number', render_kw={"placeholder": "1"})

class CutForm(Form):
    start = StringField('Start', render_kw={"value": "0"})
    end = StringField('End', render_kw={"value": "2147483647"})
    cut_type = SelectField('Cut type', choices=[(0, 'SNAPNUMBER'), (1, 'SNAPTIME'), (2, 'SNAPCOUNT')], default=1)
    client_num = StringField('Client number<sup>*</sup>', render_kw={"placeholder": "0"})


class RenderForm(Form):
    title = StringField('Title')
    gtv_match_id = HiddenField('gtv_match_id')
    map_number = HiddenField('map_number')
    filename = HiddenField('filename')
