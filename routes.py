from flask import render_template, flash, redirect, url_for, request
from app import app, db
from models import User, Product, CartItem, Order, OrderItem, Promotion
from forms import RegistrationForm, LoginForm, ProductForm, AddToCartForm
from admin_forms import DummyCSRFForm
from flask_login import current_user, login_user, logout_user, login_required, LoginManager # Necesitarás instalar Flask-Login
from sqlalchemy import func

# Configuración de Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # La vista a la que redirigir si no está logueado

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Rutas de Autenticación ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('login'))
        login_user(user) # Inicia sesión el usuario
        next_page = request.args.get('next') # Redirige a la página que intentaba acceder
        return redirect(next_page or url_for('index'))
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user() # Cierra sesión el usuario
    return redirect(url_for('index'))

# --- Rutas Generales ---
@app.route('/')
@app.route('/index')
def index():
    from models import Promotion, Product
    promociones = Promotion.query.all()
    if promociones:
        productos = []
        for promo in promociones:
            producto = Product.query.get(promo.product_id)
            if producto:
                productos.append({
                    'id': producto.id,
                    'nombre': producto.name,
                    'precio': promo.price,
                    'precio_descuento': promo.price_discounted,
                    'descuento': promo.discount,
                    'imagen': producto.image_url
                })
        mostrar_promos = True
    else:
        productos = Product.query.all()
        mostrar_promos = False
    form = AddToCartForm()
    return render_template('index.html', title='Home', productos=productos, form=form, mostrar_promos=mostrar_promos)

@app.route('/products')
def products():
    secction = request.args.get('secction')
    if secction:
        products = Product.query.filter_by(secction=secction).all()
    else:
        products = Product.query.all()
    return render_template('products.html', title='Products', products=products)

@app.route('/product/<int:product_id>', methods=['GET', 'POST'])
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    form = AddToCartForm()
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash('You need to log in to add items to your cart.', 'warning')
            return redirect(url_for('login'))

        quantity = form.quantity.data
        if quantity <= 0:
            flash('Quantity must be at least 1.', 'danger')
            return redirect(url_for('product_detail', product_id=product_id))

        if quantity > product.stock:
            flash(f'Not enough stock. Only {product.stock} available.', 'warning')
            return redirect(url_for('product_detail', product_id=product_id))

        cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product.id).first()
        if cart_item:
            if cart_item.quantity + quantity > product.stock:
                 flash(f'Adding this quantity exceeds available stock. Only {product.stock - cart_item.quantity} more can be added.', 'warning')
            else:
                cart_item.quantity += quantity
                flash(f'{quantity} more of {product.name} added to cart!', 'success')
        else:
            cart_item = CartItem(user_id=current_user.id, product_id=product.id, quantity=quantity)
            db.session.add(cart_item)
            flash(f'{product.name} added to cart!', 'success')
        db.session.commit()
        return redirect(url_for('cart'))
    return render_template('product_detail.html', title=product.name, product=product, form=form)

# --- Rutas de Carrito ---
@app.route('/cart')
@login_required
def cart():
    cart_items = current_user.cart_items  # <-- CORRECTO, sin paréntesis
    total_price = sum(item.product.price * item.quantity for item in cart_items)
    return render_template('cart.html', title='Shopping Cart', cart_items=cart_items, total_price=total_price)

@app.route('/cart/remove/<int:item_id>')
@login_required
def remove_from_cart(item_id):
    cart_item = CartItem.query.get_or_404(item_id)
    if cart_item.user_id != current_user.id:
        flash('You are not authorized to remove this item.', 'danger')
        return redirect(url_for('cart'))
    db.session.delete(cart_item)
    db.session.commit()
    flash('Item removed from cart.', 'info')
    return redirect(url_for('cart'))

# --- Rutas de Checkout/Pedido ---



from payment_form import PaymentForm

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    cart_items = current_user.cart_items
    if not cart_items:
        flash('Your cart is empty!', 'warning')
        return redirect(url_for('products'))

    form = PaymentForm()
    total_amount = sum(item.product.price * item.quantity for item in cart_items)

    if form.validate_on_submit():
        payment_method = form.payment_method.data
        # Crear una nueva orden con método de pago
        order = Order(user_id=current_user.id, total_amount=total_amount)
        # Guardar el método de pago en la orden (agregar campo si no existe)
        order.payment_method = payment_method
        db.session.add(order)
        db.session.commit()

        for item in cart_items:
            product = Product.query.get(item.product_id)
            if product.stock < item.quantity:
                flash(f'Not enough stock for {product.name}. Only {product.stock} available. Please adjust your cart.', 'danger')
                db.session.rollback()
                return redirect(url_for('cart'))
            order_item = OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                price=item.product.price
            )
            db.session.add(order_item)
            product.stock -= item.quantity
        for item in cart_items:
            db.session.delete(item)
        db.session.commit()
        flash('¡Tu pedido ha sido realizado exitosamente!', 'success')
        return redirect(url_for('orders'))
    return render_template('checkout.html', title='Confirmar Compra', form=form)


# Vista de pedidos para usuarios normales
@app.route('/orders')
@login_required
def orders():
    if current_user.is_admin:
        return redirect(url_for('admin_orders'))
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.order_date.desc()).all()
    return render_template('orders.html', title='My Orders', orders=orders)

# Vista de pedidos para administradores
@app.route('/admin/orders')
@login_required
def admin_orders():
    if not current_user.is_admin:
        flash('Acceso denegado. Debes ser administrador.', 'danger')
        return redirect(url_for('index'))
    orders = Order.query.order_by(Order.order_date.desc()).all()
    csrf_form = DummyCSRFForm()
    return render_template('admin/orders.html', title='Pedidos de Usuarios', orders=orders, csrf_form=csrf_form)

# Completar pedido (admin)
@app.route('/admin/order/<int:order_id>/complete', methods=['POST'])
@login_required
def complete_order(order_id):
    if not current_user.is_admin:
        flash('Acceso denegado. Debes ser administrador.', 'danger')
        return redirect(url_for('index'))
    order = Order.query.get_or_404(order_id)
    order.status = 'Completed'
    db.session.commit()
    flash(f'Pedido #{order.id} marcado como completado.', 'success')
    return redirect(url_for('admin_orders'))

@app.route('/order/<int:order_id>')
@login_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id and not current_user.is_admin:
        flash('You are not authorized to view this order.', 'danger')
        return redirect(url_for('orders'))
    return render_template('order_detail.html', title=f'Order #{order.id}', order=order)

# --- Rutas de Administración (requieren ser admin) ---
@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Access denied. You need to be an administrator.', 'danger')
        return redirect(url_for('index'))
    users = User.query.all()
    products = Product.query.all()
    orders = Order.query.all()
    return render_template('admin/dashboard.html', title='Admin Dashboard', users=users, products=products, orders=orders)

@app.route('/admin/product/new', methods=['GET', 'POST'])
@app.route('/admin/product/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
def manage_product(product_id=None):
    if not current_user.is_admin:
        flash('Access denied. You need to be an administrator.', 'danger')
        return redirect(url_for('index'))

    product = None
    if product_id:
        product = Product.query.get_or_404(product_id)
        form = ProductForm(obj=product)
    else:
        form = ProductForm()

    import os
    from werkzeug.utils import secure_filename
    if form.validate_on_submit():
        filename = None
        if form.image.data:
            filename = secure_filename(form.image.data.filename)
            img_path = os.path.join(app.root_path, 'static', 'imgs', filename)
            form.image.data.save(img_path)
        if product:
            form.populate_obj(product)
            if filename:
                product.image_url = filename
            flash('Product updated successfully!', 'success')
        else:
            new_product = Product(
                secction=form.secction.data,
                name=form.name.data,
                description=form.description.data,
                price=form.price.data,
                stock=form.stock.data,
                image_url=filename if filename else None
            )
            db.session.add(new_product)
            flash('Product added successfully!', 'success')
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    elif request.method == 'GET' and product_id:
        form.name.data = product.name
        form.description.data = product.description
        form.price.data = product.price
        form.stock.data = product.stock

    return render_template('admin/manage_product.html', title='Manage Product', form=form, product=product)

@app.route('/admin/product/delete/<int:product_id>')
@login_required
def delete_product(product_id):
    if not current_user.is_admin:
        flash('Access denied. You need to be an administrator.', 'danger')
        return redirect(url_for('index'))
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully!', 'info')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/promocion', methods=['GET', 'POST'])
@login_required
def admin_promocion():
    if not current_user.is_admin:
        flash('Acceso denegado. Debes ser administrador.', 'danger')
        return redirect(url_for('index'))

    productos = Product.query.all()
    productos_js = [{'id': p.id, 'nombre': p.name, 'precio': p.price} for p in productos]
    promociones = []
    if request.method == 'POST':
        productos_ids = request.form.getlist('producto[]')
        descuentos = request.form.getlist('descuento[]')
        precios = request.form.getlist('precio[]')
        precios_descuento = request.form.getlist('precio_descuento[]')
        promociones = []
        # Eliminar promociones anteriores
        Promotion.query.delete()
        db.session.commit()
        for i in range(len(productos_ids)):
            if productos_ids[i]:
                promo = Promotion(
                    product_id=int(productos_ids[i]),
                    discount=float(descuentos[i]),
                    price=float(precios[i]),
                    price_discounted=float(precios_descuento[i])
                )
                db.session.add(promo)
                promociones.append({
                    'producto_id': int(productos_ids[i]),
                    'nombre': next((p.name for p in productos if p.id == int(productos_ids[i])), ''),
                    'descuento': float(descuentos[i]),
                    'precio': float(precios[i]),
                    'precio_descuento': float(precios_descuento[i])
                })
        db.session.commit()
        flash('Promociones actualizadas correctamente.', 'success')
    else:
        # Mostrar promociones actuales
        promociones_db = Promotion.query.all()
        for promo in promociones_db:
            nombre = next((p.name for p in productos if p.id == promo.product_id), '')
            promociones.append({
                'producto_id': promo.product_id,
                'nombre': nombre,
                'descuento': promo.discount,
                'precio': promo.price,
                'precio_descuento': promo.price_discounted
            })
    return render_template('admin/promocion.html', productos=productos, promociones=promociones, productos_js=productos_js)