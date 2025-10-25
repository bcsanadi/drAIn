#!/bin/bash

echo "🌊 Setting up drAIn project..."

# Check if pip3 is available
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install Python 3 and pip3 first."
    exit 1
fi

# Install requirements
echo "📦 Installing Python packages..."
pip3 install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "🔑 Creating .env file..."
    echo "# Add your OpenAI API key here for the chatbot functionality" > .env
    echo "OPENAI_API_KEY=your-openai-api-key-here" >> .env
    echo "✅ Created .env file. Please add your OpenAI API key to enable chatbot functionality."
else
    echo "✅ .env file already exists."
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "To run the application:"
echo "1. Main app: python3 app.py (runs on port 5001)"
echo "2. Chatbot: python3 chatbot.py (runs on port 5000)"
echo ""
echo "📝 Don't forget to add your OpenAI API key to the .env file for chatbot functionality!"
