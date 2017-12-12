from flask_wtf import Form
from wtforms import TextField, SubmitField
from wtforms import validators, ValidationError


class PostForm(Form):
   update = TextField("update text", [validators.Required("Please enter text.")])
   submit = SubmitField("Post")