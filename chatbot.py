import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI

# --- optional: load local .env in development (ignored in prod if not present) ---
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
except Exception:
    pass
# -------------------------------------------------------------------------------

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError(
        "OPENAI_API_KEY is not set. "
        "Set it in your environment or create a local .env with OPENAI_API_KEY=..."
    )

client = OpenAI(api_key=api_key)

app = Flask(__name__)
# During local dev (file:// or different origin), allow all. Tighten this before prod.
CORS(app)

MODEL_PRIMARY = "gpt-4o-mini"
MODEL_FALLBACK = "gpt-4o"

def pick_model():
    """Prefer PRIMARY; if unavailable, fall back. Non-fatal errors still return a choice."""
    for m in (MODEL_PRIMARY, MODEL_FALLBACK):
        try:
            # Test with a simple chat completion
            client.chat.completions.create(
                model=m, 
                messages=[{"role": "system", "content": "test"}], 
                max_tokens=1
            )
            print(f"✅ Using model: {m}")
            return m
        except Exception as e:
            msg = str(e).lower()
            if "model_not_found" in msg or "does not exist" in msg:
                print(f"⚠️  Model not available: {m}")
                continue
            # Other transient errors—still use this model and let /chat handle it.
            print(f"ℹ️ Non-fatal during model probe for {m}: {e}")
            return m
    return MODEL_FALLBACK

MODEL = pick_model()

@app.post("/chat")
def chat():
    data = request.get_json(force=True) or {}
    history = data.get("messages", [])
    user_msg = data.get("message", "")

    convo = [{"role": "system", "content": "You are a friendly, concise website assistant."}]
    convo.extend(history)
    convo.append({"role": "user", "content": user_msg})

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=convo,
            max_tokens=150,
            temperature=0.7
        )
        return jsonify({"reply": response.choices[0].message.content})
    except Exception as e:
        # If model gets rejected mid-run, try fallback once
        msg = str(e).lower()
        if MODEL != MODEL_FALLBACK and ("model_not_found" in msg or "does not exist" in msg):
            try:
                response = client.chat.completions.create(
                    model=MODEL_FALLBACK,
                    messages=convo,
                    max_tokens=150,
                    temperature=0.7
                )
                return jsonify({"reply": response.choices[0].message.content})
            except Exception as e2:
                print("Error (fallback):", e2)
                return jsonify({"reply": f"Error: {str(e2)}"}), 500
        print("Error:", e)
        return jsonify({"reply": f"Error: {str(e)}"}), 500

if __name__ == "__main__":
    try:
        models = client.models.list()
        names = [m.id for m in models.data][:15]
        print("Visible models (first 15):", names)
    except Exception:
        pass
    print("✅ Chatbot server running on http://127.0.0.1:5000")
    app.run(debug=True, port=5000)

