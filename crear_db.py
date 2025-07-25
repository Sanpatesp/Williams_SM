from app import app, db
with app.app_context():
    db.create_all()
# Opcional: Crear un usuario administrador si quieres
    from models import User
    admin = User(username='Patricia', email='admin@supermarket.com', is_admin=True)
    admin.set_password('admin1970')
    db.session.add(admin)
    db.session.commit()
exit()