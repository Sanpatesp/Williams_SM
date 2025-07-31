from app import db

class Promotion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False, unique=True)
    discount = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    price_discounted = db.Column(db.Float, nullable=False)
    product = db.relationship('Product', backref='promotion')

    def __repr__(self):
        return f'<Promotion Product:{self.product_id} Discount:{self.discount}%>'
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'
    
    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)
    
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    secction = db.Column(db.String(64), nullable=False, default="Res")
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    image_url = db.Column(db.String(256))

    def __repr__(self):
        return f'<Product {self.name}>'

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    user = db.relationship('User', backref='cart_items')
    product = db.relationship('Product', backref='cart_items')

    def __repr__(self):
        return f'<CartItem User:{self.user_id} Product:{self.product_id} Quantity:{self.quantity}>'

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    order_date = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(64), default='Pending')  # e.g., Pending, Shipped, Delivered
    payment_method = db.Column(db.String(32), nullable=True)  # Nuevo campo

    user = db.relationship('User', backref='orders')
    items = db.relationship('OrderItem', backref='order')

    def __repr__(self):
        return f'<Order {self.id} User:{self.user_id}>'

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False) # Price at time of order

    product = db.relationship('Product', backref='order_items')

    def __repr__(self):
        return f'<OrderItem Order:{self.order_id} Product:{self.product_id}>'
