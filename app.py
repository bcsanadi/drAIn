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
    water_level = db.Column(db.Integer, default=50)  # Starting water level at 50%
    
    def set_password(self, password):
        """Hash and set the password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if the provided password matches the hash"""
        return check_password_hash(self.password_hash, password)
    
    def add_water(self, amount):
        """Add water to user's level (max 100%)"""
        self.water_level = min(100, self.water_level + amount)
        db.session.commit()
    
    def use_water(self, amount):
        """Remove water from user's level (min 0%)"""
        self.water_level = max(0, self.water_level - amount)
        db.session.commit()
    
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
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    if user:
        return render_template('home.html', water_level=user.water_level)
    else:
        return redirect(url_for('login'))

# Refill page route
@app.route('/refill', methods=['GET', 'POST'])
def refill():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        user = User.query.get(session['user_id'])
        if not user:
            return redirect(url_for('login'))
        
        total_water_saved = 0
        refill_type = ""
        
        # Define water values for each eco action (in liters)
        eco_action_values = {
            'short-shower': 2,
            'turn-off-water': 8,
            'broom-cleaning': 50,
            'full-loads': 30,
            'fixed-leak': 100,
            'scrape-dishes': 15
        }
        
        # Check for eco actions
        eco_actions_completed = []
        for action, value in eco_action_values.items():
            if request.form.get(action):
                total_water_saved += value
                eco_actions_completed.append(action.replace('-', ' ').title())
        
        # Check for donation
        donated = request.form.get('donated')
        if donated == 'yes':
            total_water_saved += 25  # Donation adds 25L equivalent
            refill_type = "donation and eco actions" if eco_actions_completed else "donation"
        elif eco_actions_completed:
            refill_type = "eco actions"
        
        # Check for learning actions
        shared_knowledge = request.form.get('shared-knowledge')
        read_article = request.form.get('read-article')
        learning_bonus = 0
        if shared_knowledge:
            learning_bonus += 10
        if read_article:
            learning_bonus += 15
        
        if learning_bonus > 0:
            total_water_saved += learning_bonus
            if refill_type:
                refill_type += " and learning"
            else:
                refill_type = "learning"
        
        # Convert liters to percentage (assuming 1L = 0.5% for game balance)
        water_percentage_gain = int(total_water_saved * 0.5)
        
        if water_percentage_gain > 0:
            old_level = user.water_level
            user.add_water(water_percentage_gain)
            new_level = user.water_level
            
            # Create success message
            actions_text = f"You completed {len(eco_actions_completed)} eco actions" if eco_actions_completed else ""
            if donated == 'yes':
                actions_text += " and made a donation" if actions_text else "You made a donation"
            if learning_bonus > 0:
                actions_text += " and engaged with learning content" if actions_text else "You engaged with learning content"
            
            flash(f'Amazing! {actions_text}, saving {total_water_saved}L of water! Your water level increased from {old_level}% to {new_level}%.')
        else:
            flash('Please select at least one action to refill your water supply!')
        
        return redirect(url_for('home'))
    
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
        return redirect(url_for('index') + '#signup-area')
    
    # Check if username or email already exists
    existing_user = User.query.filter(
        (User.username == username) | (User.email == email)
    ).first()
    
    if existing_user:
        if existing_user.username == username:
            flash('Username already exists! Please choose a different one.')
        else:
            flash('Email already registered! Please use a different email.')
        return redirect(url_for('index') + '#signup-area')
    
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
    # Create database tables and handle migrations
    with app.app_context():
        # First, create all tables
        db.create_all()
        
        # Check if we need to add water_level column to existing users
        try:
            # Check if the column exists by trying to query it
            with db.engine.connect() as conn:
                conn.execute(db.text("SELECT water_level FROM user LIMIT 1"))
            print("Water level column already exists!")
        except Exception:
            # Column doesn't exist, add it
            try:
                with db.engine.connect() as conn:
                    conn.execute(db.text("ALTER TABLE user ADD COLUMN water_level INTEGER DEFAULT 50"))
                    conn.commit()
                print("Added water_level column to existing users!")
            except Exception as e:
                print(f"Error adding column (might already exist): {e}")
        
        print("Database setup complete!")
    
    app.run(debug=True, host='0.0.0.0', port=5001)