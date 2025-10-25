from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this to a random secret key

# Database configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "users.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    
    def set_password(self, password):
        """Hash and set the password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if the provided password matches the hash"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

# Home/Landing page route
@app.route('/')
def index():
    return render_template('index.html')

# Login page route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Handle login form submission
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Please enter both username and password')
            return render_template('login.html')
        
        # Check if user exists in database
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            # Login successful
            session['user_id'] = user.id
            session['username'] = user.username
            session['fullname'] = user.fullname
            flash(f'Welcome back, {user.fullname}!')
            return redirect(url_for('home'))
        else:
            # Login failed
            flash('Invalid username or password!')
    
    return render_template('login.html')

# Home page (after login)
@app.route('/home')
def home():
    return render_template('home.html')

# Refill page route
@app.route('/refill')
def refill():
    return render_template('refill.html')

# Deplete page route
@app.route('/deplete')
def deplete():
    return render_template('deplete.html')

# API route for water level updates (for future use)
@app.route('/api/water-level', methods=['POST'])
def update_water_level():
    data = request.get_json()
    action = data.get('action')  # 'increase' or 'decrease'
    amount = data.get('amount', 5)
    
    # Here you could save to database or session
    # For now, just return success
    return jsonify({'status': 'success', 'action': action, 'amount': amount})

# Route for signup form submission
@app.route('/signup', methods=['POST'])
def signup():
    fullname = request.form.get('fullname')
    email = request.form.get('email')
    username = request.form.get('username')
    password = request.form.get('password')
    
    # Validate input
    if not all([fullname, email, username, password]):
        flash('All fields are required!')
        return redirect(url_for('index'))
    
    # Check if username or email already exists
    existing_user = User.query.filter(
        (User.username == username) | (User.email == email)
    ).first()
    
    if existing_user:
        if existing_user.username == username:
            flash('Username already exists! Please choose a different one.')
        else:
            flash('Email already registered! Please use a different email.')
        return redirect(url_for('index'))
    
    # Create new user
    try:
        new_user = User(
            fullname=fullname,
            email=email,
            username=username
        )
        new_user.set_password(password)  # Hash the password
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created successfully! Please log in.')
        return redirect(url_for('login'))
        
    except Exception as e:
        db.session.rollback()
        flash('An error occurred. Please try again.')
        return redirect(url_for('index'))

# Logout route
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Create database tables
    with app.app_context():
        db.create_all()
        print("Database tables created!")
    
    app.run(debug=True, host='0.0.0.0', port=5001)