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

def initialize_database():
    """Creates the database tables and populates it with initial data if needed."""
    with app.app_context():
        db.create_all() # Ensures all tables and columns exist for a new DB.
        
        try:
            # Create admin user if it doesn't exist
            if User.query.filter_by(username='admin').first() is None:
                hashed_password = generate_password_hash('admin') # Use a strong password in production
                admin_user = User(username='admin', password_hash=hashed_password, is_admin=True)
                db.session.add(admin_user)
                db.session.commit()
                print("Admin user created with username 'admin' and password 'admin'.")
        except OperationalError as e:
            if "no such column: user.is_admin" in str(e):
                print("="*60)
                print("DATABASE SCHEMA ERROR: The 'user' table is missing the 'is_admin' column.")
                print("SOLUTION: Please DELETE the 'database.db' file in your project folder and restart the application.")
                print("="*60)
            # Re-raise the exception to stop the app gracefully
            raise e

        # Populate products if the table is empty
        if Product.query.count() == 0:
            print("Product table is empty. Populating with initial products...")
            # The initial product list is now empty.
            # To add products, use the Admin Panel.
            # To restore the original list, you can get it from the project's Git history.
            initial_products = {
                # Laptops (5)
                1: {'name': 'Apple MacBook Air M2', 'price': 150000, 'old_price': 165000, 'rating': 4.9, 'description': ['Apple M2 Chip', '8GB RAM', '256GB SSD', 'Liquid Retina'], 'image': 'https://images.unsplash.com/photo-1541807084-5c52b6b3adef?w=400&h=300&fit=crop', 'category': 'Laptops'},
                2: {'name': 'Dell XPS 15', 'price': 180000, 'old_price': 200000, 'rating': 4.9, 'description': ['Intel Core i9', '32GB RAM', '1TB SSD', 'OLED Display'], 'image': 'https://images.unsplash.com/photo-1593642702821-c8da6771f0c6?w=400&h=300&fit=crop', 'category': 'Laptops'},
                3: {'name': 'Asus ROG Zephyrus G14', 'price': 190000, 'old_price': 210000, 'rating': 4.8, 'description': ['AMD Ryzen 9', '16GB RAM', '1TB SSD', 'RTX 3060'], 'image': 'https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=400&h=300&fit=crop', 'category': 'Laptops'},
                4: {'name': 'HP EliteBook 630 G10 Core i7', 'price': 95000, 'old_price': 110000, 'rating': 4.8, 'description': ['Intel Core i7', '16GB RAM', '512GB SSD'], 'image': 'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=400&h=300&fit=crop', 'category': 'Laptops'},
                5: {'name': 'Lenovo ThinkPad X1 Carbon', 'price': 165000, 'old_price': 180000, 'rating': 4.7, 'description': ['Intel Core i7', '16GB RAM', '1TB SSD', 'Lightweight'], 'image': 'https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?w=400&h=300&fit=crop', 'category': 'Laptops'},
                # Desktops (5)
                6: {'name': 'Apple iMac 24"', 'price': 180000, 'old_price': 195000, 'rating': 4.8, 'description': ['Apple M1 Chip', '8GB RAM', '256GB SSD', '4.5K Retina'], 'image': 'https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=400&h=300&fit=crop', 'category': 'Desktops'},
                7: {'name': 'Gaming PC Pro', 'price': 120000, 'old_price': 135000, 'rating': 4.9, 'description': ['Ryzen 7', '32GB RAM', '1TB NVMe SSD', 'RTX 4060'], 'image': 'https://images.unsplash.com/photo-1587202372634-32705e3bf49c?w=400&h=300&fit=crop', 'category': 'Desktops'},
                8: {'name': 'HP Envy All-in-One 34"', 'price': 220000, 'old_price': 240000, 'rating': 4.8, 'description': ['Intel Core i7', '16GB RAM', '1TB SSD', '5K Display'], 'image': 'https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=400&h=300&fit=crop', 'category': 'Desktops'},
                9: {'name': 'Alienware Aurora R15', 'price': 250000, 'old_price': 280000, 'rating': 4.9, 'description': ['Intel Core i9', '32GB RAM', '2TB SSD', 'RTX 4080'], 'image': 'https://images.unsplash.com/photo-1587202372634-32705e3bf49c?w=400&h=300&fit=crop', 'category': 'Desktops'},
                10: {'name': 'Corsair Vengeance i7400', 'price': 280000, 'old_price': 310000, 'rating': 4.9, 'description': ['Intel Core i7', '32GB DDR5', '2TB NVMe SSD', 'RTX 4070'], 'image': 'https://images.unsplash.com/photo-1587202372634-32705e3bf49c?w=400&h=300&fit=crop', 'category': 'Desktops'},
                # Accessories (5)
                11: {'name': 'Sony WH-1000XM5 Headphones', 'price': 45000, 'old_price': 52000, 'rating': 4.9, 'description': ['Noise Cancelling', 'Wireless', '30-Hour Battery'], 'image': 'https://images.unsplash.com/photo-1583394838336-acd977736f90?w=400&h=300&fit=crop', 'category': 'Accessories'},
                12: {'name': 'Logitech MX Master 3S Mouse', 'price': 12000, 'old_price': 15000, 'rating': 4.9, 'description': ['Ergonomic Design', '8K DPI Sensor', 'Quiet Clicks'], 'image': 'https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=400&h=300&fit=crop', 'category': 'Accessories'},
                13: {'name': 'Keychron K2 Mechanical Keyboard', 'price': 9500, 'old_price': 11000, 'rating': 4.8, 'description': ['Wireless/Wired', 'Gateron Switches', 'Mac & Windows'], 'image': 'https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=400&h=300&fit=crop', 'category': 'Accessories'},
                14: {'name': 'Anker 737 Power Bank', 'price': 15000, 'old_price': 18000, 'rating': 4.9, 'description': ['24,000mAh', '140W Output', 'Smart Display'], 'image': 'https://images.unsplash.com/photo-1609592426085-4c0c9e2d47c6?w=400&h=300&fit=crop', 'category': 'Accessories'},
                15: {'name': 'Logitech Z407 Bluetooth Speakers', 'price': 9000, 'old_price': 11000, 'rating': 4.5, 'description': ['80W Peak Power', 'Subwoofer', 'Wireless Control'], 'image': 'https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=400&h=300&fit=crop', 'category': 'Accessories'},
            }
            for pid, data in initial_products.items():                
                p = Product(id=pid, name=data['name'], price=data['price'], old_price=data.get('old_price'), rating=data.get('rating'), image=data['image'], category=data['category'])
                p.description_list = data.get('description', [])
                db.session.add(p)
            db.session.commit()
            print("Database populated with initial products.")

# Initialize the database when the application starts
initialize_database()

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
    initialize_database() # This will now run the product population logic
    flash('Product database has been successfully re-seeded.', 'success')
    return redirect(url_for('admin.index'))

@app.context_processor
def inject_cart_count():
    cart = session.get('cart', {})
    # Sum the quantities of all items in the cart
    cart_item_count = sum(cart.values())
    return dict(cart_item_count=cart_item_count)

@app.route('/')
def home():
    # Group products by category for display
    all_categories = [cat[0] for cat in db.session.query(Product.category).distinct().order_by(Product.category).all()]
    selected_category = request.args.get('category')

    categorized_products = {}
    query = Product.query

    if selected_category:
        # Filter for a single category
        if selected_category in all_categories:
            query = query.filter_by(category=selected_category)
            categorized_products[selected_category] = query.all()
    else:
        # Group all products by category
        categorized_products = {cat: [] for cat in all_categories}
        all_products = query.order_by(Product.category).all()
        for product in all_products:
            categorized_products[product.category].append(product)

    # For the carousel, just get the first 3 products
    carousel_products = Product.query.limit(3).all()

    return render_template('home.html', 
                           products=carousel_products, # Pass first 3 products for carousel
                           categories=all_categories, 
                           categorized_products=categorized_products,
                           selected_category=selected_category)

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

if __name__ == '__main__':
    # Open the web browser automatically
    def open_browser():
        webbrowser.open_new('http://127.0.0.1:5000/')

    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        # Open browser only on the first run, not on reloads
        Timer(1, open_browser).start()
    app.run(debug=True, host='0.0.0.0', port=5000)
