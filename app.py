from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.form import ImageUploadField
from flask_admin.contrib.sqla import ModelView
from flask_wtf.csrf import CSRFProtect, generate_csrf
from sqlalchemy.exc import OperationalError
from dotenv import load_dotenv
from flask_mail import Mail, Message
from functools import wraps
from paystack_handler import initiate_mpesa_charge
import hmac
import hashlib
import os
import re
import webbrowser
from threading import Timer

load_dotenv()

app = Flask(__name__)

# --- Security: Secret Key ---
# In production, require SECRET_KEY to be set. Only fall back to a default in development.
SECRET_KEY = os.environ.get('SECRET_KEY')
IS_PRODUCTION = os.environ.get('FLASK_ENV', 'production') == 'production'
if not SECRET_KEY:
    if IS_PRODUCTION:
        raise RuntimeError("SECRET_KEY environment variable must be set in production.")
    SECRET_KEY = 'dev-only-insecure-secret-key'
app.secret_key = SECRET_KEY

# --- Security: Cookies ---
app.config.update(
    SESSION_TYPE='filesystem',
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=IS_PRODUCTION,
)

# --- CSRF Protection ---
csrf = CSRFProtect(app)

# --- Database Configuration ---
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL or \
    'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

Session(app)
db = SQLAlchemy(app)

# --- Mail Configuration ---
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USE_SSL'] = os.environ.get('MAIL_USE_SSL', 'False').lower() == 'true'

mail = Mail(app)

# --- Validation helpers ---
EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")
PHONE_REGEX = re.compile(r"^\+?[0-9]{9,15}$")

def is_valid_email(email: str) -> bool:
    return bool(email and EMAIL_REGEX.match(email))

def is_valid_phone(phone: str) -> bool:
    return bool(phone and PHONE_REGEX.match(phone))

def is_strong_password(password: str) -> bool:
    """Minimum 8 chars, at least one letter and one number."""
    if not password or len(password) < 8:
        return False
    return bool(re.search(r"[A-Za-z]", password) and re.search(r"[0-9]", password))

# --- Auth Decorators ---
def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if 'username' not in session:
            flash('Please login to continue.', 'warning')
            return redirect(url_for('login', next=request.url))
        return view(*args, **kwargs)
    return wrapped

def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get('is_admin'):
            abort(403)
        return view(*args, **kwargs)
    return wrapped

# --- CSRF token in templates ---
@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=generate_csrf)

# Initialize the database if tables don't exist
def init_database():
    """Initialize the database tables and populate with initial data if they don't exist."""
    with app.app_context():
        db.create_all()

        if Product.query.count() == 0:
            hashed_password = generate_password_hash('admin')
            admin_user = User(username='admin', email='admin@example.com', password_hash=hashed_password, is_admin=True)
            db.session.add(admin_user)
            db.session.commit()

            initial_products = [
                {'name': 'Apple MacBook Air M2', 'price': 150000, 'old_price': 165000, 'rating': 4.9, 'description': ['Apple M2 Chip','8GB RAM','256GB SSD'], 'image': 'images/apple_macbook_air_m2.jpg', 'category': 'Laptops'},
                {'name': 'Dell XPS 15', 'price': 180000, 'old_price': 200000, 'rating': 4.9, 'description': ['Intel Core i9','32GB RAM','1TB SSD'], 'image': 'images/dell_xps_15.jpg', 'category': 'Laptops'},
                {'name': 'HP Spectre x360', 'price': 145000, 'old_price': 160000, 'rating': 4.7, 'description': ['Intel Core i7','16GB RAM','512GB SSD'], 'image': 'images/hp_spectre_x360.jpg', 'category': 'Laptops'},
                {'name': 'Lenovo ThinkPad X1 Carbon', 'price': 165000, 'old_price': 180000, 'rating': 4.7, 'description': ['Intel Core i7','16GB RAM','1TB SSD'], 'image': 'images/lenovo_thinkpad_x1_carbon.jpg', 'category': 'Laptops'},
                {'name': 'Asus ROG Zephyrus G14', 'price': 190000, 'old_price': 210000, 'rating': 4.8, 'description': ['AMD Ryzen 9','16GB RAM','1TB SSD'], 'image': 'images/asus_rog_zephyrus_g14.jpg', 'category': 'Laptops'},
                {'name': 'Apple iMac 24"', 'price': 180000, 'old_price': 195000, 'rating': 4.8, 'description': ['Apple M1 Chip','8GB RAM','256GB SSD'], 'image': 'images/apple_imac_24.jpg', 'category': 'Desktops'},
                {'name': 'Alienware Aurora R15', 'price': 250000, 'old_price': 280000, 'rating': 4.9, 'description': ['Intel Core i9','32GB RAM','2TB SSD'], 'image': 'images/alienware_aurora_r15.jpg', 'category': 'Desktops'},
                {'name': 'HP Envy All-in-One 34"', 'price': 220000, 'old_price': 240000, 'rating': 4.8, 'description': ['Intel Core i7','16GB RAM','1TB SSD'], 'image': 'images/hp_envy_all-in-one_34.jpg', 'category': 'Desktops'},
                {'name': 'Corsair Vengeance i7400', 'price': 280000, 'old_price': 310000, 'rating': 4.9, 'description': ['Intel Core i7','32GB DDR5','2TB NVMe'], 'image': 'images/gaming_pc_pro.jpg', 'category': 'Desktops'},
                {'name': 'HP Pavilion Gaming Desktop', 'price': 98000, 'old_price': 110000, 'rating': 4.6, 'description': ['Intel Core i5','16GB RAM','512GB SSD'], 'image': 'images/hp_pavilion_gaming_desktop.jpg', 'category': 'Desktops'},
                {'name': 'Sony WH-1000XM5 Headphones', 'price': 45000, 'old_price': 52000, 'rating': 4.9, 'description': ['Noise Cancelling','Wireless','30-Hour Battery'], 'image': 'images/sony_wh-1000xm5_headphones.jpg', 'category': 'Accessories'},
                {'name': 'Logitech MX Master 3S Mouse', 'price': 12000, 'old_price': 15000, 'rating': 4.9, 'description': ['Ergonomic Design','8K DPI Sensor','Quiet Clicks'], 'image': 'images/logitech_mx_master_3s_mouse.jpg', 'category': 'Accessories'},
                {'name': 'Keychron K2 Mechanical Keyboard', 'price': 9500, 'old_price': 11000, 'rating': 4.8, 'description': ['Wireless/Wired','Gateron Switches','Mac & Windows'], 'image': 'images/keychron_k2_mechanical_keyboard.jpg', 'category': 'Accessories'},
                {'name': 'Anker 737 Power Bank', 'price': 15000, 'old_price': 18000, 'rating': 4.9, 'description': ['24,000mAh','140W Output','Smart Display'], 'image': 'images/anker_737_power_bank.jpg', 'category': 'Accessories'},
                {'name': 'Logitech C920 HD Pro Webcam', 'price': 8000, 'old_price': 9500, 'rating': 4.7, 'description': ['1080p Full HD','Stereo Audio','Light Correction'], 'image': 'images/logitech_c920_hd_pro_webcam.jpg', 'category': 'Accessories'},
            ]

            for data in initial_products:
                p = Product(name=data['name'], price=data['price'], old_price=data.get('old_price'), rating=data.get('rating'), image=data['image'], category=data['category'])
                p.description_list = data.get('description', [])
                db.session.add(p)

            test_order = Order(
                user_id=admin_user.id,
                reference='TEST_ORDER_123',
                amount=150000,
                phone_number='0712345678',
                county='Nairobi',
                city='Nairobi',
                shipping_address='Test Street, Nairobi',
                status='success'
            )
            db.session.add(test_order)

            db.session.commit()
            print("✅ Database initialized with tables and initial data.")

# --- Database Models ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    old_price = db.Column(db.Float)
    rating = db.Column(db.Float)
    description = db.Column(db.String(500))
    image = db.Column(db.String(500), nullable=False)
    category = db.Column(db.String(80), nullable=False)

    @property
    def web_image_path(self):
        if self.image:
            return self.image.replace('\\', '/')
        return None

    @property
    def description_list(self):
        return self.description.split(',') if self.description else []

    @description_list.setter
    def description_list(self, value_list):
        self.description = ','.join(value_list)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reference = db.Column(db.String(100), unique=True, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    county = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    shipping_address = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(50), default='pending')
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

# --- Email Sending Functions ---
def send_welcome_email(email, username):
    if not app.config.get('MAIL_SERVER'):
        return
    msg = Message(
        subject='Welcome to Tech Kenya Accessories!',
        sender=app.config['MAIL_USERNAME'],
        recipients=[email]
    )
    msg.body = f"""
Hello {username},

Welcome to Tech Kenya Accessories! Thank you for registering with us.

You can now log in to your account and start shopping for the best tech products.

Best regards,
The Tech Kenya Team
"""
    try:
        mail.send(msg)
    except Exception as e:
        print(f"Failed to send welcome email to {email}: {e}")

def send_login_notification(email, username):
    if not app.config.get('MAIL_SERVER'):
        return
    msg = Message(
        subject='Login Notification - Tech Kenya Accessories',
        sender=app.config['MAIL_USERNAME'],
        recipients=[email]
    )
    msg.body = f"""
Hello {username},

This is a notification that you have successfully logged in to your Tech Kenya account.

If this was not you, please contact our support team immediately.

Best regards,
The Tech Kenya Team
"""
    try:
        mail.send(msg)
    except Exception as e:
        print(f"Failed to send login notification to {email}: {e}")

@app.cli.command('init-db')
def init_db_command():
    """Clears the existing data and creates new tables with fresh product data."""
    with app.app_context():
        db.drop_all()
        db.create_all()

        hashed_password = generate_password_hash('admin')
        admin_user = User(username='admin', email='admin@example.com', password_hash=hashed_password, is_admin=True)
        db.session.add(admin_user)

        initial_products = [
            {'name': 'Apple MacBook Air M2', 'price': 150000, 'old_price': 165000, 'rating': 4.9, 'description': ['Apple M2 Chip','8GB RAM','256GB SSD'], 'image': 'images/apple_macbook_air_m2.jpg', 'category': 'Laptops'},
            {'name': 'Dell XPS 15', 'price': 180000, 'old_price': 200000, 'rating': 4.9, 'description': ['Intel Core i9','32GB RAM','1TB SSD'], 'image': 'images/dell_xps_15.jpg', 'category': 'Laptops'},
            {'name': 'HP Spectre x360', 'price': 145000, 'old_price': 160000, 'rating': 4.7, 'description': ['Intel Core i7','16GB RAM','512GB SSD'], 'image': 'images/hp_spectre_x360.jpg', 'category': 'Laptops'},
            {'name': 'Lenovo ThinkPad X1 Carbon', 'price': 165000, 'old_price': 180000, 'rating': 4.7, 'description': ['Intel Core i7','16GB RAM','1TB SSD'], 'image': 'images/lenovo_thinkpad_x1_carbon.jpg', 'category': 'Laptops'},
            {'name': 'Asus ROG Zephyrus G14', 'price': 190000, 'old_price': 210000, 'rating': 4.8, 'description': ['AMD Ryzen 9','16GB RAM','1TB SSD'], 'image': 'images/asus_rog_zephyrus_g14.jpg', 'category': 'Laptops'},
            {'name': 'Apple iMac 24"', 'price': 180000, 'old_price': 195000, 'rating': 4.8, 'description': ['Apple M1 Chip','8GB RAM','256GB SSD'], 'image': 'images/apple_imac_24.jpg', 'category': 'Desktops'},
            {'name': 'Alienware Aurora R15', 'price': 250000, 'old_price': 280000, 'rating': 4.9, 'description': ['Intel Core i9','32GB RAM','2TB SSD'], 'image': 'images/alienware_aurora_r15.jpg', 'category': 'Desktops'},
            {'name': 'HP Envy All-in-One 34"', 'price': 220000, 'old_price': 240000, 'rating': 4.8, 'description': ['Intel Core i7','16GB RAM','1TB SSD'], 'image': 'images/hp_envy_all-in-one_34.jpg', 'category': 'Desktops'},
            {'name': 'Corsair Vengeance i7400', 'price': 280000, 'old_price': 310000, 'rating': 4.9, 'description': ['Intel Core i7','32GB DDR5','2TB NVMe'], 'image': 'images/gaming_pc_pro.jpg', 'category': 'Desktops'},
            {'name': 'HP Pavilion Gaming Desktop', 'price': 98000, 'old_price': 110000, 'rating': 4.6, 'description': ['Intel Core i5','16GB RAM','512GB SSD'], 'image': 'images/hp_pavilion_gaming_desktop.jpg', 'category': 'Desktops'},
            {'name': 'Sony WH-1000XM5 Headphones', 'price': 45000, 'old_price': 52000, 'rating': 4.9, 'description': ['Noise Cancelling','Wireless','30-Hour Battery'], 'image': 'images/sony_wh-1000xm5_headphones.jpg', 'category': 'Accessories'},
            {'name': 'Logitech MX Master 3S Mouse', 'price': 12000, 'old_price': 15000, 'rating': 4.9, 'description': ['Ergonomic Design','8K DPI Sensor','Quiet Clicks'], 'image': 'images/logitech_mx_master_3s_mouse.jpg', 'category': 'Accessories'},
            {'name': 'Keychron K2 Mechanical Keyboard', 'price': 9500, 'old_price': 11000, 'rating': 4.8, 'description': ['Wireless/Wired','Gateron Switches','Mac & Windows'], 'image': 'images/keychron_k2_mechanical_keyboard.jpg', 'category': 'Accessories'},
            {'name': 'Anker 737 Power Bank', 'price': 15000, 'old_price': 18000, 'rating': 4.9, 'description': ['24,000mAh','140W Output','Smart Display'], 'image': 'images/anker_737_power_bank.jpg', 'category': 'Accessories'},
            {'name': 'Logitech C920 HD Pro Webcam', 'price': 8000, 'old_price': 9500, 'rating': 4.7, 'description': ['1080p Full HD','Stereo Audio','Light Correction'], 'image': 'images/logitech_c920_hd_pro_webcam.jpg', 'category': 'Accessories'},
        ]

        for data in initial_products:
            p = Product(name=data['name'], price=data['price'], old_price=data.get('old_price'), rating=data.get('rating'), image=data['image'], category=data['category'])
            p.description_list = data.get('description', [])
            db.session.add(p)

        db.session.commit()
        print("✅ Initialized the database with fresh data.")

@app.route('/admin/reseed-products', methods=['POST'])
@login_required
@admin_required
def reseed_products():
    """Admin-only POST route to clear and re-populate the product database."""
    db.session.query(Product).delete()
    db.session.commit()
    flash('All products deleted. Repopulating database...', 'warning')
    init_db_command.callback()
    flash('Product database has been successfully re-seeded.', 'success')
    return redirect(url_for('admin.index'))

@app.context_processor
def inject_cart_count():
    cart = session.get('cart', {})
    cart_item_count = sum(cart.values())

    cart_items = []
    total = 0
    for pid_str, qty in cart.items():
        pid = int(pid_str)
        product = Product.query.get(pid)
        if product:
            subtotal = product.price * qty
            total += subtotal
            cart_items.append({
                'id': pid,
                'name': product.name,
                'price': product.price,
                'quantity': qty,
                'subtotal': subtotal,
                'image': product.web_image_path
            })

    return dict(
        cart_item_count=cart_item_count,
        cart_items=cart_items,
        cart_total=total
    )

@app.route('/')
def home():
    search_query = request.args.get('q')
    selected_category = request.args.get('category')

    query = Product.query

    if search_query:
        query = query.filter(Product.name.ilike(f'%{search_query}%'))
        selected_category = None
    elif selected_category:
        query = query.filter_by(category=selected_category)

    products = query.order_by(Product.name).all()
    all_categories = [cat[0] for cat in db.session.query(Product.category).distinct().order_by(Product.category).all()]

    categorized_products = {}
    if products:
        result_categories = sorted(list(set(p.category for p in products)))
        for cat in result_categories:
            categorized_products[cat] = [p for p in products if p.category == cat]

    carousel_products = Product.query.limit(3).all()

    return render_template('home.html',
                           carousel_products=carousel_products,
                           categories=all_categories,
                           categorized_products=categorized_products,
                           selected_category=selected_category,
                           search_query=search_query)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    related_products = Product.query.filter(
        Product.category == product.category,
        Product.id != product.id
    ).limit(4).all()
    return render_template('product_detail.html', product=product, related_products=related_products)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        email = (request.form.get('email') or '').strip().lower()
        password = request.form.get('password') or ''

        if not username or not email or not password:
            flash('Username, email, and password are required.', 'warning')
            return redirect(url_for('register'))

        if not is_valid_email(email):
            flash('Please enter a valid email address.', 'warning')
            return redirect(url_for('register'))

        if not is_strong_password(password):
            flash('Password must be at least 8 characters and contain both letters and numbers.', 'warning')
            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'warning')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'warning')
            return redirect(url_for('register'))

        new_user = User(username=username, email=email, password_hash=generate_password_hash(password))
        db.session.add(new_user)
        db.session.commit()
        send_welcome_email(new_user.email, new_user.username)
        flash('Registration successful. Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        password = request.form.get('password') or ''
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            session.clear()
            session['username'] = username
            session['is_admin'] = user.is_admin
            flash('Login successful', 'success')
            send_login_notification(user.email, user.username)
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials', 'danger')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/add_to_cart/<int:product_id>')
def add_to_cart(product_id):
    product = Product.query.get(product_id)
    if not product:
        flash('Product not found.', 'danger')
        return redirect(request.referrer or url_for('home'))

    cart = session.get('cart', {})
    product_id_str = str(product_id)
    cart[product_id_str] = cart.get(product_id_str, 0) + 1
    session['cart'] = cart
    flash(f"'{product.name}' added to cart.", 'info')
    return redirect(request.referrer or url_for('home'))

@app.route('/remove_from_cart/<int:product_id>')
def remove_from_cart(product_id):
    cart = session.get('cart', {})
    product_id_str = str(product_id)

    if product_id_str in cart:
        product = Product.query.get(product_id)
        product_name = product.name if product else 'Item'
        cart.pop(product_id_str, None)
        session['cart'] = cart
        flash(f"'{product_name}' removed from cart.", 'info')
    else:
        flash('Item not found in cart.', 'warning')

    return redirect(url_for('cart'))

@app.route('/update_cart/<int:product_id>', methods=['POST'])
def update_cart(product_id):
    cart = session.get('cart', {})
    product_id_str = str(product_id)

    try:
        quantity = int(request.form.get('quantity'))
    except (ValueError, TypeError):
        flash('Invalid quantity.', 'danger')
        return redirect(url_for('cart'))

    if quantity <= 0:
        flash('Quantity must be at least 1.', 'warning')
        return redirect(url_for('cart'))

    if product_id_str in cart:
        cart[product_id_str] = quantity
        session['cart'] = cart
        flash('Cart updated.', 'success')

    return redirect(url_for('cart'))

@app.route('/cart')
def cart():
    cart = session.get('cart', {})
    cart_items = []
    total = 0
    for pid_str, qty in cart.items():
        pid = int(pid_str)
        product = Product.query.get(pid)
        if product:
            subtotal = product.price * qty
            total += subtotal
            cart_items.append({'id': pid, 'name': product.name, 'price': product.price, 'quantity': qty, 'subtotal': subtotal})
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    if not session.get('cart'):
        flash('Your cart is empty. Add items before checking out.', 'warning')
        return redirect(url_for('home'))

    admin_phone = '0111214624'

    if request.method == 'POST':
        phone_number = (request.form.get('phone_number') or '').strip()
        county = (request.form.get('county') or '').strip()
        city = (request.form.get('city') or '').strip()
        shipping_address = (request.form.get('shipping_address') or '').strip()

        # Override phone for admin user
        if session.get('is_admin'):
            phone_number = admin_phone

        if not is_valid_phone(phone_number):
            flash('Please provide a valid M-PESA phone number.', 'warning')
            return render_template('checkout.html', admin_phone=admin_phone)

        if not county or not city or not shipping_address:
            flash('Please provide complete shipping details.', 'warning')
            return render_template('checkout.html', admin_phone=admin_phone)

        # Recalculate total from DB to prevent client tampering
        cart = session.get('cart', {})
        total = 0
        for pid_str, qty in cart.items():
            product = Product.query.get(int(pid_str))
            if product and qty > 0:
                total += product.price * qty

        if total <= 0:
            flash('Cannot checkout with an empty cart.', 'warning')
            return redirect(url_for('cart'))

        user = User.query.filter_by(username=session['username']).first()
        if not user:
            flash('User not found. Please log in again.', 'danger')
            return redirect(url_for('logout'))

        # Initiate payment
        email = user.email or "customer@example.com"
        result = initiate_mpesa_charge(phone_number=phone_number, amount=total, email=email)

        if isinstance(result, dict) and "error" in result:
            reference = f"ANORLD_{int(total)}_{re.sub(r'[^0-9]', '', phone_number)}"
            order = Order(
                user_id=user.id,
                reference=reference,
                amount=total,
                phone_number=phone_number,
                county=county,
                city=city,
                shipping_address=shipping_address,
                status='failed'
            )
            db.session.add(order)
            db.session.commit()
            flash(f'Payment initiation failed: {result["error"]}. Order {reference} created for tracking.', 'danger')
            return render_template('checkout.html', admin_phone=admin_phone)

        reference = result.get('data', {}).get('reference') if isinstance(result, dict) else None
        if not reference:
            flash('Payment provider did not return a reference. Please try again.', 'danger')
            return render_template('checkout.html', admin_phone=admin_phone)

        order = Order(
            user_id=user.id,
            reference=reference,
            amount=total,
            phone_number=phone_number,
            county=county,
            city=city,
            shipping_address=shipping_address,
            status='pending'
        )
        db.session.add(order)
        db.session.commit()

        flash(f'A payment request has been sent to {phone_number}. Please enter your M-PESA PIN to complete the transaction. Order: {reference}', 'success')
        session.pop('cart', None)

        return redirect(url_for('home'))
    return render_template('checkout.html', admin_phone=admin_phone)

@app.route('/mpesa_callback', methods=['POST'])
def mpesa_callback():
    # Safaricom will POST transaction status here. Signature verification
    # should be added once production credentials are available.
    data = request.get_json(silent=True) or {}
    print(f"M-PESA callback received: {data}")
    return 'OK', 200

@app.route('/paystack_webhook', methods=['POST'])
@csrf.exempt
def paystack_webhook():
    """Verify Paystack webhook signature before processing events."""
    paystack_secret_key = os.environ.get('PAYSTACK_SECRET_KEY')
    if not paystack_secret_key:
        return 'Server misconfiguration', 500

    signature = request.headers.get('x-paystack-signature', '')
    body = request.get_data() or b''
    expected = hmac.new(
        paystack_secret_key.encode('utf-8'),
        body,
        hashlib.sha512
    ).hexdigest()

    if not hmac.compare_digest(expected, signature):
        return 'Invalid signature', 400

    data = request.get_json(silent=True) or {}
    event = data.get('event')
    reference = (data.get('data') or {}).get('reference')

    if event in ('charge.success', 'charge.failed') and reference:
        order = Order.query.filter_by(reference=reference).first()
        if order:
            order.status = 'success' if event == 'charge.success' else 'failed'
            db.session.commit()
            print(f"Order {reference} marked as {order.status}.")
        else:
            print(f"Order with reference {reference} not found.")

    return 'OK', 200

@app.route('/orders')
@login_required
def orders():
    user = User.query.filter_by(username=session['username']).first()
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('logout'))
    user_orders = Order.query.filter_by(user_id=user.id).order_by(Order.created_at.desc()).all()
    return render_template('orders.html', orders=user_orders)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = (request.form.get('name') or '').strip()
        email = (request.form.get('email') or '').strip().lower()
        category = (request.form.get('category') or '').strip()
        message = (request.form.get('message') or '').strip()

        if not name or not email or not category or not message:
            flash('All fields are required.', 'warning')
            return redirect(url_for('contact'))

        if not is_valid_email(email):
            flash('Please enter a valid email address.', 'warning')
            return redirect(url_for('contact'))

        flash(f'Thank you {name}, your {category} message has been sent. We will get back to you at {email}.', 'success')
        return redirect(url_for('home'))
    return render_template('contact.html')

# --- Admin Configuration ---
class SecureModelView(ModelView):
    """Model view that requires admin privileges."""
    def is_accessible(self):
        return session.get('is_admin') is True

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login', next=request.url))

upload_path = os.path.join(os.path.dirname(__file__), 'static/images')
try:
    os.makedirs(upload_path)
except OSError:
    pass

class ProductAdminView(SecureModelView):
    form_overrides = {
        'image': ImageUploadField
    }
    form_args = {
        'image': {
            'label': 'Image',
            'base_path': upload_path,
            'url_relative_path': 'images/'
        }
    }

admin = Admin(app, name='Tech Kenya Admin')
admin.add_view(SecureModelView(User, db.session))
admin.add_view(ProductAdminView(Product, db.session))

init_database()

if __name__ == '__main__':
    def open_browser():
        webbrowser.open_new('http://127.0.0.1:5000/')

    # Only auto-open browser in development
    if not IS_PRODUCTION and os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        Timer(1, open_browser).start()
    port = int(os.environ.get('PORT', 10000))
    app.run(debug=False, host='0.0.0.0', port=port)