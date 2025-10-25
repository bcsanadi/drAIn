import os, json
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI

# Get API key from environment variable
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set")
client = OpenAI(api_key=api_key)

app = Flask(__name__)
CORS(app)

MODEL_PRIMARY = "gpt-4o-mini"
MODEL_FALLBACK = "gpt-4o"

def pick_model():
    # try primary; if not found, try fallback
    for m in (MODEL_PRIMARY, MODEL_FALLBACK):
        try:
            # lightweight no-op call to check availability (list is heavier; skip if you want)
            client.responses.create(model=m, input=[{"role":"system","content":"ok"}], max_output_tokens=1)
            print(f"✅ Using model: {m}")
            return m
        except Exception as e:
            if "model_not_found" in str(e) or "does not exist" in str(e):
                print(f"⚠️  Model not available: {m}")
                continue
            else:
                # other transient errors: still use this model and let /chat handle
                print(f"ℹ️ Non-fatal during model probe for {m}: {e}")
                return m
    # last resort
    return MODEL_FALLBACK

MODEL = pick_model()

@app.post("/chat")
def chat():
    data = request.get_json(force=True) or {}
    history = data.get("messages", [])
    user_msg = data.get("message", "")

    convo = [{"role":"system","content":"You are a friendly, concise website assistant."}]
    convo.extend(history)
    convo.append({"role":"user","content": user_msg})

    try:
        r = client.responses.create(model=MODEL, input=convo)
        return jsonify({"reply": r.output_text})
    except Exception as e:
        # If model gets rejected mid-run, try the fallback once
        if MODEL != MODEL_FALLBACK and ("model_not_found" in str(e) or "does not exist" in str(e)):
            try:
                r = client.responses.create(model=MODEL_FALLBACK, input=convo)
                return jsonify({"reply": r.output_text})
            except Exception as e2:
                print("Error (fallback):", e2)
                return jsonify({"reply": f"Error: {str(e2)}"}), 500
        print("Error:", e)
        return jsonify({"reply": f"Error: {str(e)}"}), 500

if __name__ == "__main__":
    # Optional: show a few models you have access to
    try:
        models = client.models.list()
        names = [m.id for m in models.data][:15]
        print("Visible models (first 15):", names)
    except Exception as _:
        pass
    print("✅ Chatbot server running on http://127.0.0.1:5000")
    app.run(debug=True, port=5000)


