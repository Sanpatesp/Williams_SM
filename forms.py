from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, FloatField, IntegerField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length
from models import User, Product

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class ProductForm(FlaskForm):
    name = StringField('Product Name', validators=[DataRequired(), Length(min=2, max=128)])
    description = TextAreaField('Description')
    price = FloatField('Price', validators=[DataRequired()])
    stock = IntegerField('Stock', validators=[DataRequired()])
    image_url = StringField('Image URL')
    submit = SubmitField('Add/Update Product')

class AddToCartForm(FlaskForm):
    quantity = IntegerField('Quantity', validators=[DataRequired()])
    submit = SubmitField('Add to Cart')