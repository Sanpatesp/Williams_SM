import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'una-cadena-muy-dificil-de-adivinar'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'site.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False