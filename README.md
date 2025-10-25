# drAIn 🌊
*Your personal water conservation companion*

Gatorhack - AI Days

## About
drAIn is a web application that gamifies water conservation by combining interactive features, educational content, and AI-powered assistance. Users can track their water usage, learn about conservation techniques, and get personalized advice through our integrated chatbot.

## Features
- 🏠 **User Dashboard**: Track your water conservation level
- 💧 **Refill System**: Gain water points through eco-friendly actions and donations
- 🤖 **AI Chatbot**: Get personalized water conservation advice
- 📚 **Educational Resources**: Learn about water conservation techniques
- 🎮 **Gamification**: Make conservation fun with progress tracking

## Quick Setup

### Option 1: Automatic Setup (Recommended)
```bash
chmod +x setup.sh
./setup.sh
```

### Option 2: Manual Setup
1. **Install Dependencies**
   ```bash
   pip3 install -r requirements.txt
   ```

2. **Set up Environment Variables**
   - Create a `.env` file in the project root
   - Add your OpenAI API key:
   ```
   OPENAI_API_KEY=your-openai-api-key-here
   ```

3. **Run the Applications**
   - Main app: `python3 app.py` (runs on port 5001)
   - Chatbot: `python3 chatbot.py` (runs on port 5000)

## Project Structure
```
drAIn/
├── app.py                 # Main Flask application
├── chatbot.py            # OpenAI chatbot server
├── requirements.txt      # Python dependencies
├── setup.sh             # Automated setup script
├── users.db             # SQLite database
├── templates/           # HTML templates
│   ├── index.html       # Landing/signup page
│   ├── login.html       # Login page
│   ├── home.html        # User dashboard
│   ├── refill.html      # Water refill actions
│   └── deplete.html     # Chatbot interface
├── static/
│   ├── css/style.css    # Main stylesheet
│   └── fonts/           # Custom fonts
└── Fonts/
    └── TAN MERINGUE.ttf # Custom title font
```

## Dependencies
- Flask 2.3.3
- Flask-SQLAlchemy 3.0.5
- OpenAI 2.6.1
- Flask-CORS 6.0.1
- python-dotenv 1.1.1
- And more (see requirements.txt)

## Usage
1. **Sign Up**: Create an account on the landing page
2. **Login**: Access your dashboard
3. **Refill**: Complete eco-actions to increase your water level
4. **Chat**: Get AI-powered conservation advice
5. **Track Progress**: Monitor your conservation journey

## API Key Setup
To use the chatbot functionality, you'll need an OpenAI API key:
1. Visit [OpenAI](https://platform.openai.com/api-keys)
2. Create an API key
3. Add it to your `.env` file

## Contributing
Built with 🩵 by Scrumpty Dumpty for Gatorhack - AI Days

## License
This project is for educational purposes.