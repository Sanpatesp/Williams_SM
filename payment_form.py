from flask_wtf import FlaskForm
from wtforms import RadioField, SubmitField
from wtforms.validators import DataRequired

class PaymentForm(FlaskForm):
    payment_method = RadioField('Método de Pago', choices=[
        ('efectivo', 'Efectivo'),
        ('tarjeta', 'Tarjeta'),
        ('transferencia', 'Transferencia Bancaria')
    ], validators=[DataRequired()])
    submit = SubmitField('Confirmar Compra')
