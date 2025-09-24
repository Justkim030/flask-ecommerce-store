from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.form import ImageUploadField
from flask_admin.contrib.sqla import ModelView
from sqlalchemy.exc import OperationalError
from dotenv import load_dotenv
import webbrowser
from threading import Timer
from mpesa_handler import initiate_stk_push # Import the M-PESA function
import os

load_dotenv() # Load environment variables from .env file

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'a-default-fallback-secret-key-for-dev')
app.config['SESSION_TYPE'] = 'filesystem'

# --- Database Configuration ---
# Use PostgreSQL in production (on Render) and SQLite for local development
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL or \
    'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

Session(app)
db = SQLAlchemy(app)

# Initialize the database if tables don't exist
def init_database():
    """Initialize the database tables and populate with initial data if they don't exist."""
    with app.app_context():
        try:
            # Check if tables exist by trying to query them
            db.session.execute(db.text('SELECT 1 FROM product LIMIT 1'))
        except Exception:
            # Tables don't exist, create them
            db.create_all()

            # Create admin user
            hashed_password = generate_password_hash('admin')
            admin_user = User(username='admin', password_hash=hashed_password, is_admin=True)
            db.session.add(admin_user)

            # Populate with initial products
            initial_products = [
                # Laptops
                {'name': 'Apple MacBook Air M2', 'price': 150000, 'old_price': 165000, 'rating': 4.9, 'description': ['Apple M2 Chip','8GB RAM','256GB SSD'], 'image': 'images/apple_macbook_air_m2.jpg', 'category': 'Laptops'},
                {'name': 'Dell XPS 15', 'price': 180000, 'old_price': 200000, 'rating': 4.9, 'description': ['Intel Core i9','32GB RAM','1TB SSD'], 'image': 'images/dell_xps_15.jpg', 'category': 'Laptops'},
                {'name': 'HP Spectre x360', 'price': 145000, 'old_price': 160000, 'rating': 4.7, 'description': ['Intel Core i7','16GB RAM','512GB SSD'], 'image': 'images/hp_spectre_x360.jpg', 'category': 'Laptops'},
                {'name': 'Lenovo ThinkPad X1 Carbon', 'price': 165000, 'old_price': 180000, 'rating': 4.7, 'description': ['Intel Core i7','16GB RAM','1TB SSD'], 'image': 'images/lenovo_thinkpad_x1_carbon.jpg', 'category': 'Laptops'},
                {'name': 'Asus ROG Zephyrus G14', 'price': 190000, 'old_price': 210000, 'rating': 4.8, 'description': ['AMD Ryzen 9','16GB RAM','1TB SSD'], 'image': 'images/asus_rog_zephyrus_g14.jpg', 'category': 'Laptops'},

                # Desktops
                {'name': 'Apple iMac 24"', 'price': 180000, 'old_price': 195000, 'rating': 4.8, 'description': ['Apple M1 Chip','8GB RAM','256GB SSD'], 'image': 'images/apple_imac_24.jpg', 'category': 'Desktops'},
                {'name': 'Alienware Aurora R15', 'price': 250000, 'old_price': 280000, 'rating': 4.9, 'description': ['Intel Core i9','32GB RAM','2TB SSD'], 'image': 'images/alienware_aurora_r15.jpg', 'category': 'Desktops'},
                {'name': 'HP Envy All-in-One 34"', 'price': 220000, 'old_price': 240000, 'rating': 4.8, 'description': ['Intel Core i7','16GB RAM','1TB SSD'], 'image': 'images/hp_envy_all-in-one_34.jpg', 'category': 'Desktops'},
                {'name': 'Corsair Vengeance i7400', 'price': 280000, 'old_price': 310000, 'rating': 4.9, 'description': ['Intel Core i7','32GB DDR5','2TB NVMe'], 'image': 'images/gaming_pc_pro.jpg', 'category': 'Desktops'},
                {'name': 'HP Pavilion Gaming Desktop', 'price': 98000, 'old_price': 110000, 'rating': 4.6, 'description': ['Intel Core i5','16GB RAM','512GB SSD'], 'image': 'images/hp_pavilion_gaming_desktop.jpg', 'category': 'Desktops'},

                # Accessories
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
            print("✅ Database initialized with tables and initial data.")

# --- Database Models ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    old_price = db.Column(db.Float)
    rating = db.Column(db.Float)
    description = db.Column(db.String(500)) # Storing as comma-separated string
    image = db.Column(db.String(500), nullable=False)
    category = db.Column(db.String(80), nullable=False)

    @property
    def web_image_path(self):
        """Ensures the image path uses forward slashes for web URLs."""
        if self.image:
            return self.image.replace('\\', '/')
        return None

    # Helper to convert description from/to list
    @property
    def description_list(self):
        return self.description.split(',') if self.description else []

    @description_list.setter
    def description_list(self, value_list):
        self.description = ','.join(value_list)

@app.cli.command('init-db')
def init_db_command():
    """Clears the existing data and creates new tables with fresh product data."""
    with app.app_context():
        db.drop_all()
        db.create_all()

        # Create admin user
        hashed_password = generate_password_hash('admin')
        admin_user = User(username='admin', password_hash=hashed_password, is_admin=True)
        db.session.add(admin_user)

        # This list uses local image paths to guarantee they load.
        initial_products = [
            # Laptops
            {'name': 'Apple MacBook Air M2', 'price': 150000, 'old_price': 165000, 'rating': 4.9, 'description': ['Apple M2 Chip','8GB RAM','256GB SSD'], 'image': 'images/apple_macbook_air_m2.jpg', 'category': 'Laptops'},
            {'name': 'Dell XPS 15', 'price': 180000, 'old_price': 200000, 'rating': 4.9, 'description': ['Intel Core i9','32GB RAM','1TB SSD'], 'image': 'images/dell_xps_15.jpg', 'category': 'Laptops'},
            {'name': 'HP Spectre x360', 'price': 145000, 'old_price': 160000, 'rating': 4.7, 'description': ['Intel Core i7','16GB RAM','512GB SSD'], 'image': 'images/hp_spectre_x360.jpg', 'category': 'Laptops'},
            {'name': 'Lenovo ThinkPad X1 Carbon', 'price': 165000, 'old_price': 180000, 'rating': 4.7, 'description': ['Intel Core i7','16GB RAM','1TB SSD'], 'image': 'images/lenovo_thinkpad_x1_carbon.jpg', 'category': 'Laptops'},
            {'name': 'Asus ROG Zephyrus G14', 'price': 190000, 'old_price': 210000, 'rating': 4.8, 'description': ['AMD Ryzen 9','16GB RAM','1TB SSD'], 'image': 'images/asus_rog_zephyrus_g14.jpg', 'category': 'Laptops'},
            
            # Desktops
            {'name': 'Apple iMac 24"', 'price': 180000, 'old_price': 195000, 'rating': 4.8, 'description': ['Apple M1 Chip','8GB RAM','256GB SSD'], 'image': 'images/apple_imac_24.jpg', 'category': 'Desktops'},
            {'name': 'Alienware Aurora R15', 'price': 250000, 'old_price': 280000, 'rating': 4.9, 'description': ['Intel Core i9','32GB RAM','2TB SSD'], 'image': 'images/alienware_aurora_r15.jpg', 'category': 'Desktops'},
            {'name': 'HP Envy All-in-One 34"', 'price': 220000, 'old_price': 240000, 'rating': 4.8, 'description': ['Intel Core i7','16GB RAM','1TB SSD'], 'image': 'images/hp_envy_all-in-one_34.jpg', 'category': 'Desktops'},
            {'name': 'Corsair Vengeance i7400', 'price': 280000, 'old_price': 310000, 'rating': 4.9, 'description': ['Intel Core i7','32GB DDR5','2TB NVMe'], 'image': 'images/gaming_pc_pro.jpg', 'category': 'Desktops'},
            {'name': 'HP Pavilion Gaming Desktop', 'price': 98000, 'old_price': 110000, 'rating': 4.6, 'description': ['Intel Core i5','16GB RAM','512GB SSD'], 'image': 'images/hp_pavilion_gaming_desktop.jpg', 'category': 'Desktops'},

            # Accessories
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

@app.route('/admin/reseed-products')
def reseed_products():
    """
    An admin-only route to clear and re-populate the product database.
    This is useful for development to apply changes from initial_products.
    """
    if not session.get('is_admin'):
        flash('You do not have permission to perform this action.', 'danger')
        return redirect(url_for('home'))

    # Clear the Product table
    db.session.query(Product).delete()
    db.session.commit()
    flash('All products have been deleted. Repopulating database...', 'warning')
    init_db_command() # This will now run the product population logic
    flash('Product database has been successfully re-seeded.', 'success')
    return redirect(url_for('admin.index'))

@app.context_processor
def inject_cart_count():
    cart = session.get('cart', {})
    # Sum the quantities of all items in the cart
    cart_item_count = sum(cart.values())

    # Get cart items for dropdown display
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
    # Get search query and category from request args
    search_query = request.args.get('q')
    selected_category = request.args.get('category')

    # Base query
    query = Product.query

    # Apply search filter if present
    if search_query:
        query = query.filter(Product.name.ilike(f'%{search_query}%'))
        # When searching, we don't want the category filter from the sidebar to be active
        selected_category = None

    # Apply category filter if present (and not searching)
    elif selected_category:
        query = query.filter_by(category=selected_category)

    # Fetch products from the filtered query
    products = query.order_by(Product.name).all()

    # Get all distinct categories for the sidebar
    all_categories = [cat[0] for cat in db.session.query(Product.category).distinct().order_by(Product.category).all()]

    # Group the final list of products by category for display
    categorized_products = {}
    if products:
        result_categories = sorted(list(set(p.category for p in products)))
        for cat in result_categories:
            categorized_products[cat] = [p for p in products if p.category == cat]

    # For the carousel, just get the first 3 products
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
    # You could also fetch related products here to show on the page
    related_products = Product.query.filter(
        Product.category == product.category, 
        Product.id != product.id
    ).limit(4).all()
    return render_template('product_detail.html', product=product, related_products=related_products)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash('Username and password are required.', 'warning')
            return redirect(url_for('register'))
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists', 'warning')
            return redirect(url_for('register'))

        new_user = User(username=username, password_hash=generate_password_hash(password))
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful. Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            session['username'] = username
            session['is_admin'] = user.is_admin
            flash('Login successful', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials', 'danger')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('is_admin', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/add_to_cart/<int:product_id>')
def add_to_cart(product_id):
    product = Product.query.get(product_id)
    if not product:
        flash('Product not found.', 'danger')
        return redirect(request.referrer or url_for('home'))

    cart = session.get('cart', {})
    # Use string keys for the cart session dictionary for JSON compatibility
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
        # Get product name before deleting for the flash message
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

    if product_id_str in cart:
        if quantity > 0:
            cart[product_id_str] = quantity
            flash('Cart updated.', 'success')
        else: # If quantity is 0 or less, remove the item
            cart.pop(product_id_str, None)
            flash('Item removed from cart.', 'info')
        session['cart'] = cart

    return redirect(url_for('cart'))

@app.route('/cart')
def cart():
    cart = session.get('cart', {})
    cart_items = []
    total = 0
    for pid_str, qty in cart.items():
        # Convert the string key from the session back to an integer for product lookup
        pid = int(pid_str)
        product = Product.query.get(pid)
        if product:
            subtotal = product.price * qty
            total += subtotal
            cart_items.append({'id': pid, 'name': product.name, 'price': product.price, 'quantity': qty, 'subtotal': subtotal})
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'username' not in session:
        flash('Please login to checkout.', 'warning')
        return redirect(url_for('login'))
    
    if not session.get('cart'):
        flash('Your cart is empty. Add items before checking out.', 'warning')
        return redirect(url_for('home'))

    admin_phone = '0111214624' # Admin's predefined M-PESA number

    if request.method == 'POST':
        phone_number = request.form.get('phone_number')
        
        # 1. Calculate total amount from the cart
        cart = session.get('cart', {})
        total = 0
        for pid_str, qty in cart.items():
            product = Product.query.get(int(pid_str))
            if product:
                total += product.price * qty

        # Override phone number if the user is an admin
        if session.get('is_admin'):
            phone_number = admin_phone
            flash('Admin checkout: Using predefined M-PESA number.', 'info')

        if total == 0:
            flash('Cannot checkout with an empty cart.', 'warning')
            return redirect(url_for('cart'))

        # 2. Initiate the STK Push (fire and forget)
        initiate_stk_push(phone_number=phone_number, amount=total)

        # 3. Always flash a success message and clear the cart, regardless of the API response.
        flash(f'A payment request has been sent to {phone_number}. Please enter your M-PESA PIN to complete the transaction.', 'success')
        session.pop('cart', None)

        return redirect(url_for('home'))
    return render_template('checkout.html', admin_phone=admin_phone)

@app.route('/mpesa_callback', methods=['POST'])
def mpesa_callback():
    # M-PESA will send a POST request to this URL after a transaction.
    # You need to process the JSON data to confirm payment status.
    data = request.get_json()
    # Logic to update order status in the database based on the callback data.
    return 'OK', 200

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        category = request.form.get('category')
        message = request.form.get('message')

        if not name or not email or not category or not message:
            flash('All fields are required.', 'warning')
            return redirect(url_for('contact'))

        # Here you can add logic to send an email or save to database
        # For now, just flash a success message
        flash(f'Thank you {name}, your {category} message has been sent. We will get back to you at {email}.', 'success')
        return redirect(url_for('home'))
    return render_template('contact.html')

# --- Admin Configuration ---
class SecureModelView(ModelView):
    """Create a secure model view that requires admin privileges."""
    def is_accessible(self):
        return session.get('is_admin') is True

    def inaccessible_callback(self, name, **kwargs):
        # Redirect non-admin users to the login page
        return redirect(url_for('login', next=request.url))

# --- Custom Admin View for Products with Image Upload ---
# Define the path for image uploads relative to the app's root directory
upload_path = os.path.join(os.path.dirname(__file__), 'static/images')
# Create the directory if it doesn't exist
try:
    os.makedirs(upload_path)
except OSError:
    pass

class ProductAdminView(SecureModelView):
    # Use form_overrides for the class and form_args for constructor arguments
    # This is the standard and most stable way to configure custom fields.
    form_overrides = {
        'image': ImageUploadField
    }
    form_args = {
        'image': {
            'label': 'Image',
            'base_path': upload_path,
            'url_relative_path': 'images/' # Ensures correct URL generation
        }
    }

admin = Admin(app, name='Tech Kenya Admin', template_mode='bootstrap4')
admin.add_view(SecureModelView(User, db.session))
# Replace the default Product view with our new custom one
admin.add_view(ProductAdminView(Product, db.session))

# Initialize database on startup
init_database()

if __name__ == '__main__':
    # Open the web browser automatically
    def open_browser():
        webbrowser.open_new('http://127.0.0.1:5000/')

    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        # Open browser only on the first run, not on reloads
        Timer(1, open_browser).start()
    app.run(debug=True, host='0.0.0.0', port=5000)
