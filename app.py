import os
from datetime import datetime, timezone
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify # type: ignore
from flask_sqlalchemy import SQLAlchemy # type: ignore
from werkzeug.security import generate_password_hash, check_password_hash # type: ignore

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev")

# Database configuration
basedir = os.path.abspath(os.path.dirname(__file__))
db_url = os.environ.get("DATABASE_URL")
if db_url:
    # Make sure we use the psycopg v3 driver
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+psycopg://", 1)
    elif db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(basedir, 'users.db')}"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize database
db = SQLAlchemy(app)

# User model
class User(db.Model):
    __tablename__ = "users"  # <-- necessary for Postgres (avoid reserved word)
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    water_level = db.Column(db.Integer, default=50)  # Starting water level at 50%
    
    # Relationship to user actions
    actions = db.relationship('UserAction', backref='user', lazy=True, cascade='all, delete-orphan')
    
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

class UserAction(db.Model):
    __tablename__ = "user_actions"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # <-- match users.id
    action_type = db.Column(db.String(50), nullable=False)  # 'eco', 'donation', 'learning', 'deplete'
    action_name = db.Column(db.String(100), nullable=False)  # specific action like 'short-shower'
    water_amount = db.Column(db.Float, nullable=False)  # liters saved/used
    percentage_change = db.Column(db.Integer, nullable=False)  # percentage change in water level
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    def __repr__(self):
        return f'<UserAction {self.action_name}: {self.water_amount}L>'

# --- Ensure tables exist on Render (gunicorn import) ---
with app.app_context():
    db.create_all()

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
        
        old_level = user.water_level  # Initialize old_level at the start
        total_water_saved = 0
        refill_type = ""
        
        # Define water values for each eco action (in liters)
        eco_action_values = {
            'short-shower': 5,
            'turn-off-water': 1.5,
            'broom-cleaning': 50,
            'full-loads': 3,
            'scrape-dishes': 9
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
        # Use max(1, ...) to ensure at least 1% gain for any water saved
        water_percentage_gain = max(1, int(total_water_saved * 0.5)) if total_water_saved > 0 else 0
        
        if water_percentage_gain > 0:
            user.add_water(water_percentage_gain)
            new_level = user.water_level
            
            # Record individual eco actions
            for action, value in eco_action_values.items():
                if request.form.get(action):
                    action_record = UserAction(
                        user_id=user.id,
                        action_type='eco',
                        action_name=action.replace('-', ' ').title(),
                        water_amount=value,
                        percentage_change=int(value * 0.5)
                    )
                    db.session.add(action_record)
            
            # Record donation if made
            if donated == 'yes':
                donation_record = UserAction(
                    user_id=user.id,
                    action_type='donation',
                    action_name='Donation',
                    water_amount=25,
                    percentage_change=12
                )
                db.session.add(donation_record)
            
            # Record learning actions
            if shared_knowledge:
                learning_record = UserAction(
                    user_id=user.id,
                    action_type='learning',
                    action_name='Shared Knowledge',
                    water_amount=10,
                    percentage_change=5
                )
                db.session.add(learning_record)
            
            if read_article:
                learning_record = UserAction(
                    user_id=user.id,
                    action_type='learning',
                    action_name='Read Article',
                    water_amount=15,
                    percentage_change=7
                )
                db.session.add(learning_record)
            
            # Commit all actions to database
            db.session.commit()
            
            # Create success message
            actions_text = f"You completed {len(eco_actions_completed)} eco actions" if eco_actions_completed else ""
            if donated == 'yes':
                actions_text += " and made a donation" if actions_text else "You made a donation"
            if learning_bonus > 0:
                actions_text += " and engaged with learning content" if actions_text else "You engaged with learning content"
            
            flash(f'Amazing! {actions_text}, saving {total_water_saved}L of water! Your water level increased from {old_level}% to {new_level}%.')
        else:
            flash('Please select at least one action to refill your water supply!')
        
        return redirect(url_for('home', refilled='true', old_level=old_level))
    
    return render_template('refill.html')

# Specific refill routes for different actions
@app.route('/refill/eco', methods=['POST'])
def refill_eco():
    return refill()

@app.route('/refill/learn', methods=['POST'])
def refill_learn():
    return refill()

@app.route('/refill/donate', methods=['POST'])
def refill_donate():
    return refill()

# Deplete page route
@app.route('/deplete')
def deplete():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    if not user:
        return redirect(url_for('login'))
    
    return render_template('deplete.html', water_level=user.water_level)

# Learn More page route - displays the impact comparison chart
@app.route('/learn_more')
def learn_more():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('learn_more.html')

# Progress page route - displays dynamic graphs
@app.route('/progress')
def progress():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get the real user's water level
    user = User.query.get(session['user_id'])
    if not user:
        return redirect(url_for('login'))
    
    return render_template('progress.html', water_level=user.water_level)

# API route to get user progress data for graphs
@app.route('/api/user-progress')
def get_user_progress():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user_id = session['user_id']
    
    # Get all user actions
    actions = UserAction.query.filter_by(user_id=user_id).all()
    
    # Calculate action totals
    action_totals = {}
    for action in actions:
        action_name = action.action_name
        if action_name not in action_totals:
            action_totals[action_name] = {
                'total_water': 0,
                'total_percentage': 0,
                'count': 0
            }
        
        action_totals[action_name]['total_water'] += action.water_amount
        action_totals[action_name]['total_percentage'] += action.percentage_change
        action_totals[action_name]['count'] += 1
    
    # If no actions yet, provide an empty structure
    if not action_totals:
        action_totals = {
            'Short Shower': {'total_water': 0, 'total_percentage': 0, 'count': 0},
            'Turn Off Water': {'total_water': 0, 'total_percentage': 0, 'count': 0},
            'Broom Cleaning': {'total_water': 0, 'total_percentage': 0, 'count': 0},
            'Full Loads': {'total_water': 0, 'total_percentage': 0, 'count': 0},
            'Scrape Dishes': {'total_water': 0, 'total_percentage': 0, 'count': 0}
        }
    
    return jsonify({'action_totals': action_totals})

# API route to get water level history
@app.route('/api/water-level-history')
def get_water_level_history():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Get user actions ordered by timestamp
    actions = UserAction.query.filter_by(user_id=user_id).order_by(UserAction.timestamp).all()
    
    # Build history working backwards from current actual level
    # This ensures the graph ends at the correct current level
    actual_level = user.water_level
    
    if not actions:
        # No actions yet, just show current level
        history = [{'timestamp': 'Current', 'water_level': actual_level, 'action': 'Current Level'}]
    else:
        # Calculate total change from actions
        total_action_change = sum(action.percentage_change for action in actions)
        
        # Work backwards: if current level is X and total change is Y, starting level was X-Y
        starting_level = actual_level - total_action_change
        
        # Build history starting from calculated starting level
        history = [{'timestamp': 'Start', 'water_level': starting_level, 'action': 'Initial Level'}]
        current_level = starting_level
        
        for action in actions:
            current_level = min(100, max(0, current_level + action.percentage_change))
            history.append({
                'timestamp': action.timestamp.strftime('%m/%d %H:%M'),
                'water_level': current_level,
                'action': action.action_name
            })
        
        # Ensure final level matches actual level (should be the case, but just in case)
        if history[-1]['water_level'] != actual_level:
            history[-1]['water_level'] = actual_level
    
    # Debug output to help track the issue
    print(f"DEBUG History: User actual level: {actual_level}%, Action count: {len(actions)}, Final history level: {history[-1]['water_level']}%")
    
    return jsonify({
        'history': history,
        'current_level': user.water_level
    })

# API route for water level updates (for future use)
@app.route('/api/water-level', methods=['POST'])
def update_water_level():
    data = request.get_json()
    action = data.get('action')  # 'increase' or 'decrease'
    amount = data.get('amount', 5)
    
    # Here you could save to database or session
    # For now, just return success
    return jsonify({'status': 'success', 'action': action, 'amount': amount})

# API route to track chatbot interactions and water depletion
@app.route('/api/track-chatbot', methods=['POST'])
def track_chatbot_interaction():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    try:
        data = request.get_json()
        user_message = data.get('user_message', '')
        bot_response = data.get('bot_response', '')
        
        # Calculate word count (user message + bot response)
        user_words = len(user_message.split())
        bot_words = len(bot_response.split())
        total_words = user_words + bot_words
        
        # Calculate water depletion: 519 mL per 100 words
        water_depleted_ml = (total_words / 100) * 519
        water_depleted_liters = water_depleted_ml / 1000
        
        # Fixed percentage decrease: 5% per chatbot interaction
        percentage_decrease = 5
        
        print(f"DEBUG: Total words: {total_words}, User words: {user_words}, Bot words: {bot_words}")
        print(f"DEBUG: Water depleted: {water_depleted_ml}mL ({water_depleted_liters:.3f}L), Percentage: {percentage_decrease}%")
        
        # Get user and update water level
        user = User.query.get(session['user_id'])
        if user:
            old_level = user.water_level
            print(f"DEBUG: User water level before: {old_level}%")
            user.use_water(percentage_decrease)
            new_level = user.water_level
            print(f"DEBUG: User water level after: {new_level}%")
            
            # Record the depletion action
            depletion_record = UserAction(
                user_id=user.id,
                action_type='deplete',
                action_name='Chatbot Interaction',
                water_amount=-water_depleted_liters,  # negative for depletion
                percentage_change=-percentage_decrease  # negative for decrease
            )
            db.session.add(depletion_record)
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'user_words': user_words,
                'bot_words': bot_words,
                'words_processed': total_words,
                'water_depleted_ml': round(water_depleted_ml, 2),
                'water_depleted_liters': round(water_depleted_liters, 3),
                'percentage_decrease': percentage_decrease,
                'old_water_level': old_level,
                'new_water_level': new_level
            })
        else:
            return jsonify({'error': 'User not found'}), 404
                        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
                conn.execute(db.text("SELECT water_level FROM users LIMIT 1"))  # <-- users
            print("Water level column already exists!")
        except Exception:
            # Column doesn't exist, add it
            try:
                with db.engine.connect() as conn:
                    conn.execute(db.text("ALTER TABLE users ADD COLUMN water_level INTEGER DEFAULT 50"))  # <-- users
                    conn.commit()
                print("Added water_level column to existing users!")
            except Exception as e:
                print(f"Error adding column (might already exist): {e}")
        
        print("Database setup complete!")
    
    app.run(debug=True, host='0.0.0.0', port=5001)
    #testing
