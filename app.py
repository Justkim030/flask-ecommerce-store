from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
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
            initial_products = {
                1: {'name': 'HP ProBook 445 14" G11 Notebook', 'price': 85000, 'old_price': 95000, 'rating': 4.5, 'description': ['AMD R5-7535U', '8GB RAM', '512GB SSD'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=HP+ProBook', 'category': 'Laptops'},
                2: {'name': 'HP EliteBook 630 G10 Core i7', 'price': 95000, 'old_price': 110000, 'rating': 4.8, 'description': ['Intel Core i7', '16GB RAM', '512GB SSD'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=HP+EliteBook', 'category': 'Laptops'},
                3: {'name': 'Lenovo V14 Gen2 14" Intel', 'price': 75000, 'old_price': 82000, 'rating': 4.2, 'description': ['Intel Core i5', '8GB RAM', '256GB SSD'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=Lenovo+V14', 'category': 'Laptops'},
                4: {'name': 'TP-Link Archer C6 WiFi Router', 'price': 5000, 'old_price': 6500, 'rating': 4.6, 'description': ['Dual Band', '4 Antennas', 'Gigabit Ports'], 'image': 'wifirouters-2048px-3572.webp', 'category': 'Accessories'},
                5: {'name': 'Office Gadgets Set', 'price': 3000, 'old_price': 3500, 'rating': 4.1, 'description': ['Desk Organizer', 'Phone Stand', 'Cable Clips'], 'image': 'gh-office-gadgets-66042b2e9168c.avif', 'category': 'Accessories'},
                6: {'name': 'Gaming PC Pro', 'price': 120000, 'old_price': 135000, 'rating': 4.9, 'description': ['Ryzen 7', '32GB RAM', '1TB NVMe SSD', 'RTX 4060'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=Gaming+PC', 'category': 'Desktops'},
                7: {'name': 'Laptop Accessory Kit', 'price': 2500, 'old_price': 3000, 'rating': 4.3, 'description': ['Laptop Sleeve', 'USB Hub', 'Mini Mouse'], 'image': 'download.jpg', 'category': 'Accessories'},
                8: {'name': 'Logitech MX Master 3S Mouse', 'price': 12000, 'old_price': 15000, 'rating': 4.9, 'description': ['Ergonomic Design', '8K DPI Sensor', 'Quiet Clicks'], 'image': 'download (1).jpg', 'category': 'Accessories'},
                9: {'name': 'Keychron K2 Mechanical Keyboard', 'price': 9500, 'old_price': 11000, 'rating': 4.8, 'description': ['Wireless/Wired', 'Gateron Switches', 'Mac & Windows'], 'image': 'download (2).jpg', 'category': 'Accessories'},
                10: {'name': 'SanDisk Ultra 128GB USB Drive', 'price': 1500, 'old_price': 2000, 'rating': 4.9, 'description': ['USB 3.0', '130MB/s Speed', 'Portable'], 'image': 'download (3).jpg', 'category': 'Accessories'},
                11: {'name': 'Samsung T7 1TB External SSD', 'price': 11000, 'old_price': 13000, 'rating': 4.8, 'description': ['USB-C', 'Portable SSD', '1,050 MB/s Speed'], 'image': 'download (4).jpg', 'category': 'Accessories'},
                12: {'name': 'Logitech C920 HD Pro Webcam', 'price': 8000, 'old_price': 9500, 'rating': 4.7, 'description': ['1080p Full HD', 'Stereo Audio', 'Light Correction'], 'image': 'download (5).jpg', 'category': 'Accessories'},
                13: {'name': 'Sony WH-1000XM5 Headphones', 'price': 45000, 'old_price': 52000, 'rating': 4.9, 'description': ['Noise Cancelling', 'Wireless', '30-Hour Battery'], 'image': 'download (6).jpg', 'category': 'Accessories'},
                14: {'name': 'Dell XPS 15', 'price': 180000, 'old_price': 200000, 'rating': 4.9, 'description': ['Intel Core i9', '32GB RAM', '1TB SSD', 'OLED Display'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=Dell+XPS+15', 'category': 'Laptops'},
                15: {'name': 'Apple MacBook Air M2', 'price': 150000, 'old_price': 165000, 'rating': 4.9, 'description': ['Apple M2 Chip', '8GB RAM', '256GB SSD', 'Liquid Retina'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=MacBook+Air', 'category': 'Laptops'},
                16: {'name': 'Lenovo ThinkPad X1 Carbon', 'price': 165000, 'old_price': 180000, 'rating': 4.7, 'description': ['Intel Core i7', '16GB RAM', '1TB SSD', 'Lightweight'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=ThinkPad+X1', 'category': 'Laptops'},
                17: {'name': 'Asus ROG Zephyrus G14', 'price': 190000, 'old_price': 210000, 'rating': 4.8, 'description': ['AMD Ryzen 9', '16GB RAM', '1TB SSD', 'RTX 3060'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=Asus+ROG', 'category': 'Laptops'},
                18: {'name': 'Microsoft Surface Laptop 5', 'price': 130000, 'old_price': 140000, 'rating': 4.6, 'description': ['Intel Core i5', '8GB RAM', '512GB SSD', 'Touchscreen'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=Surface+Laptop', 'category': 'Laptops'},
                19: {'name': 'Acer Swift 3', 'price': 88000, 'old_price': 98000, 'rating': 4.4, 'description': ['AMD Ryzen 7', '8GB RAM', '512GB SSD', '14" FHD IPS'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=Acer+Swift+3', 'category': 'Laptops'},
                20: {'name': 'HP Spectre x360', 'price': 145000, 'old_price': 160000, 'rating': 4.7, 'description': ['Intel Core i7', '16GB RAM', '512GB SSD', '2-in-1 Convertible'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=HP+Spectre', 'category': 'Laptops'},
                21: {'name': 'Apple iMac 24"', 'price': 180000, 'old_price': 195000, 'rating': 4.8, 'description': ['Apple M1 Chip', '8GB RAM', '256GB SSD', '4.5K Retina'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=iMac+24', 'category': 'Desktops'},
                22: {'name': 'HP Pavilion Gaming Desktop', 'price': 98000, 'old_price': 110000, 'rating': 4.6, 'description': ['Intel Core i5', '16GB RAM', '512GB SSD', 'GTX 1660 Super'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=HP+Pavilion', 'category': 'Desktops'},
                23: {'name': 'Dell Inspiron Compact Desktop', 'price': 65000, 'old_price': 75000, 'rating': 4.3, 'description': ['Intel Core i5', '12GB RAM', '256GB SSD', 'Small Form Factor'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=Dell+Inspiron', 'category': 'Desktops'},
                24: {'name': 'Lenovo IdeaCentre AIO 3', 'price': 85000, 'old_price': 95000, 'rating': 4.5, 'description': ['AMD Ryzen 5', '8GB RAM', '512GB SSD', '24" FHD Display'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=Lenovo+AIO', 'category': 'Desktops'},
                25: {'name': 'Alienware Aurora R15', 'price': 250000, 'old_price': 280000, 'rating': 4.9, 'description': ['Intel Core i9', '32GB RAM', '2TB SSD', 'RTX 4080'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=Alienware', 'category': 'Desktops'},
                26: {'name': 'Intel NUC Mini PC', 'price': 55000, 'old_price': 62000, 'rating': 4.7, 'description': ['Intel Core i7', '16GB RAM', '512GB NVMe', 'Ultra Compact'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=Intel+NUC', 'category': 'Desktops'},
                27: {'name': 'HP Envy All-in-One 34"', 'price': 220000, 'old_price': 240000, 'rating': 4.8, 'description': ['Intel Core i7', '16GB RAM', '1TB SSD', '5K Display'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=HP+Envy+AIO', 'category': 'Desktops'},
                28: {'name': 'Office Workstation PC', 'price': 78000, 'old_price': 85000, 'rating': 4.4, 'description': ['Intel Core i7', '16GB RAM', '1TB HDD + 256GB SSD'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=Office+PC', 'category': 'Desktops'},
                29: {'name': 'Mac Mini M2', 'price': 90000, 'old_price': 100000, 'rating': 4.8, 'description': ['Apple M2 Chip', '8GB RAM', '256GB SSD', 'Compact Power'], 'image': 'download (5).jpg', 'category': 'Desktops'},
                30: {'name': 'Dell UltraSharp 27" 4K Monitor', 'price': 65000, 'old_price': 75000, 'rating': 4.8, 'description': ['27-inch 4K UHD', 'IPS Panel', 'USB-C Hub'], 'image': 'download (7).jpg', 'category': 'Accessories'},
                31: {'name': 'Anker 737 Power Bank', 'price': 15000, 'old_price': 18000, 'rating': 4.9, 'description': ['24,000mAh', '140W Output', 'Smart Display'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=Anker+Power+Bank', 'category': 'Accessories'},
                32: {'name': 'SteelSeries QcK Mousepad', 'price': 2000, 'old_price': 2500, 'rating': 4.8, 'description': ['Large Size', 'Micro-Woven Cloth', 'Non-slip Base'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=Mousepad', 'category': 'Accessories'},
                33: {'name': 'HP LaserJet Pro M404dn', 'price': 35000, 'old_price': 40000, 'rating': 4.6, 'description': ['Monochrome Laser', 'Fast Printing', 'Network Ready'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=HP+LaserJet', 'category': 'Accessories'},
                34: {'name': 'Logitech Z407 Bluetooth Speakers', 'price': 9000, 'old_price': 11000, 'rating': 4.5, 'description': ['80W Peak Power', 'Subwoofer', 'Wireless Control'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=Logitech+Speakers', 'category': 'Accessories'},
                35: {'name': 'Rain Design mStand Laptop Stand', 'price': 5500, 'old_price': 6500, 'rating': 4.9, 'description': ['Ergonomic', 'Aluminum Design', 'Cable Organizer'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=Laptop+Stand', 'category': 'Accessories'},
                36: {'name': 'Razer Blade 15', 'price': 220000, 'old_price': 240000, 'rating': 4.8, 'description': ['Intel Core i7', '16GB RAM', '1TB SSD', 'RTX 3070Ti'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=Razer+Blade', 'category': 'Laptops'},
                37: {'name': 'LG Gram 17', 'price': 160000, 'old_price': 175000, 'rating': 4.6, 'description': ['Intel Core i7', '16GB RAM', '1TB SSD', 'Ultra-lightweight'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=LG+Gram', 'category': 'Laptops'},
                38: {'name': 'Samsung Galaxy Book3 Pro', 'price': 155000, 'old_price': 170000, 'rating': 4.7, 'description': ['Intel Core i7', '16GB RAM', '512GB SSD', 'AMOLED 2X'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=Galaxy+Book3', 'category': 'Laptops'},
                39: {'name': 'Framework Laptop 13', 'price': 140000, 'old_price': 150000, 'rating': 4.9, 'description': ['Intel Core i5', '16GB RAM', '512GB SSD', 'Repairable'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=Framework', 'category': 'Laptops'},
                40: {'name': 'Google Pixelbook Go', 'price': 95000, 'old_price': 110000, 'rating': 4.5, 'description': ['Intel Core i5', '8GB RAM', '128GB SSD', 'ChromeOS'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=Pixelbook+Go', 'category': 'Laptops'},
                41: {'name': 'Corsair Vengeance i7400', 'price': 280000, 'old_price': 310000, 'rating': 4.9, 'description': ['Intel Core i7', '32GB DDR5', '2TB NVMe SSD', 'RTX 4070'], 'image': 'download (6).jpg', 'category': 'Desktops'},
                42: {'name': 'MSI Trident AS', 'price': 210000, 'old_price': 230000, 'rating': 4.7, 'description': ['Intel Core i7', '16GB RAM', '1TB SSD', 'RTX 3060Ti'], 'image': 'download (7).jpg', 'category': 'Desktops'},
                43: {'name': 'HP Omen 45L', 'price': 260000, 'old_price': 290000, 'rating': 4.8, 'description': ['AMD Ryzen 9', '32GB RAM', '1TB SSD + 1TB HDD', 'RTX 4070Ti'], 'image': 'images.jpg', 'category': 'Desktops'},
                44: {'name': 'NZXT Player: Two', 'price': 190000, 'old_price': 205000, 'rating': 4.7, 'description': ['AMD Ryzen 5', '16GB RAM', '1TB NVMe SSD', 'RTX 3070'], 'image': 'images (1).jpg', 'category': 'Desktops'},
                45: {'name': 'Lenovo Legion Tower 5i', 'price': 175000, 'old_price': 190000, 'rating': 4.6, 'description': ['Intel Core i7', '16GB RAM', '512GB SSD + 1TB HDD'], 'image': 'images (2).jpg', 'category': 'Desktops'},
            }
            for pid, data in initial_products.items():                
                p = Product(id=pid, name=data['name'], price=data['price'], old_price=data.get('old_price'), rating=data.get('rating'), image=data['image'], category=data['category'])
                p.description_list = data.get('description', [])
                db.session.add(p)
            db.session.commit()
            print("Database populated with initial products.")

# Initialize the database when the application starts
initialize_database()

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

admin = Admin(app, name='Tech Kenya Admin', template_mode='bootstrap4')
admin.add_view(SecureModelView(User, db.session))
admin.add_view(SecureModelView(Product, db.session))

if __name__ == '__main__':
    # Open the web browser automatically
    def open_browser():
        webbrowser.open_new('http://127.0.0.1:5000/')

    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        # Open browser only on the first run, not on reloads
        Timer(1, open_browser).start()
    app.run(debug=True, host='0.0.0.0', port=5000)
