from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this to a random secret key

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
        
        # Add your login logic here
        # For now, just redirect to home
        if username and password:
            session['username'] = username
            return redirect(url_for('home'))
        else:
            flash('Please enter both username and password')
    
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
    
    # Add your signup logic here
    # For now, just redirect to login
    flash('Account created successfully! Please log in.')
    return redirect(url_for('login'))

# Logout route
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)