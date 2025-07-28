from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config
from flask_migrate import Migrate

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
# Importar rutas al final para evitar problemas de importación circular
from routes import *

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)