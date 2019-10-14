from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired

class BasicForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    color = StringField('Color', validators=[DataRequired()])
    submit = SubmitField('Submit Information')
