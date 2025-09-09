# Tech Kenya Accessories Store

A simple online store built with Flask that allows customers to register, browse products, add items to a shopping cart, and checkout.

## Features

- User registration and login with password hashing.
- Product listing with categories and filtering.
- Dynamic shopping cart with add, remove, and update quantity functionality.
- Persistent data storage using an SQLite database.
- Admin panel for managing users and products.
- Checkout with M-PESA payment (simulated).
- Styled with a custom, Kilimall-inspired theme using Bootstrap.

## Requirements

- Python 3.7+
- Flask
- Flask-Session
- Flask-SQLAlchemy
- Flask-Admin
- gunicorn (for deployment)
- python-dotenv (for managing environment variables)

## Installation

1. Clone or download the project files.
2. Navigate to the project directory in your terminal.
3. Create a virtual environment:
   ```bash
   python -m venv venv
   ```
4. Activate the virtual environment:
   - On Windows: `venv\Scripts\activate`
   - On macOS/Linux: `source venv/bin/activate`
5. Install the required packages into your virtual environment:
   ```bash
   pip install -r requirements.txt
   ```
6. Create a `.env` file for your local environment variables by copying the example:
   - On Windows (Command Prompt): `copy .env.example .env`
   - On macOS/Linux: `cp .env.example .env`
   
   *You can modify the `SECRET_KEY` in your new `.env` file for better security.*

## Running the Application

1. Make sure your virtual environment is activated.
2. Run the Flask app:
   ```bash
   python app.py
   ```
3. The first time you run the app, the SQLite database (`database.db`) will be automatically created and populated with sample products and a default admin user.
4. Open your browser and go to `http://127.0.0.1:5000`

### Admin Access

- **URL**: `http://127.0.0.1:5000/admin`
- **Username**: `admin`
- **Password**: `admin`

## Deployment

This app is ready for deployment to hosting platforms like Render or Heroku.

You will need a `Procfile` in your root directory with the following content:
```
web: python app.py
```

And set the environment variable `FLASK_APP=app.py`.

## Non-Functional Requirements Addressed

- **Durability**: Data is stored in an SQLite database (`database.db`) for local development. The app is configured to use PostgreSQL for production environments.
- **Usable**: Simple, intuitive interface with Bootstrap styling.
- **Available**: Flask app can be run continuously on hosting platforms.
- **Attractive**: Clean, responsive design using Bootstrap.
- **Hosted on free platform**: Can be deployed to free tiers of Heroku or PythonAnywhere.

## Note

This is a demonstration application. For a full production deployment, the primary remaining task is to integrate a real M-PESA payment gateway API.
