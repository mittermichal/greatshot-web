from flask_wtf import FlaskForm
from wtforms import StringField, FileField, SelectField, HiddenField, IntegerField
# from wtforms.fields.html5 import IntegerField


class ExportFileForm(FlaskForm):
    file = FileField('Demo')


class CutForm(FlaskForm):
    start = IntegerField('Start', default=0, render_kw={"step": "50"})
    end = IntegerField('End', default=2147483000, render_kw={"step": "50"})
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

