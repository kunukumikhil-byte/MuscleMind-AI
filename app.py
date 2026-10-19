"""MuscleMind-AI Flask application, configured for Vercel Python functions."""
import os
import sqlite3
import re
import math
from functools import wraps

from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database import connect_db, create_tables

load_dotenv()

app = Flask(__name__)
_secret = os.getenv("SECRET_KEY")
if not _secret:
    if os.getenv("VERCEL") == "1" or os.getenv("FLASK_ENV") == "production":
        raise RuntimeError("SECRET_KEY must be configured in deployment environment variables.")
    _secret = "local-development-only-not-for-production"
app.secret_key = _secret
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.getenv("VERCEL") == "1" or os.getenv("FLASK_ENV") == "production",
)

# SQLite is useful for local development. On Vercel, /tmp is writable but ephemeral;
# use a managed database for persistent production data.
create_tables()


def get_groq_client():
    """Create the AI client only when needed so a missing key won't crash app import."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not configured. Add it in Vercel Project Settings > Environment Variables."
        )
    from groq import Groq
    return Groq(api_key=api_key)


def get_google_oauth():
    """Return configured Google OAuth client, or None when credentials are absent."""
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    if not client_id or not client_secret:
        return None
    from authlib.integrations.flask_client import OAuth
    oauth = OAuth(app)
    return oauth.register(
        name="google",
        client_id=client_id,
        client_secret=client_secret,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )


google = get_google_oauth()


def login_required():
    return "user_id" in session


def ai_completion(prompt):
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("Enter a message first.")
    if len(prompt) > 8000:
        raise ValueError("Request is too long. Please shorten it to 8,000 characters or fewer.")
    key = os.getenv("GROQ_API_KEY", "").strip()
    if not key:
        raise RuntimeError("AI service is not configured.")
    model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b").strip()
    if model.lower() in {"groq_model", "your_model_name", "model_name"} or not model:
        model = "openai/gpt-oss-120b"
    from groq import Groq
    client = Groq(api_key=key, timeout=30.0, max_retries=1)
    result = client.chat.completions.create(
        model=model,
        messages=[
            {"role":"system","content":"You are MuscleMind AI, a safety-conscious fitness and nutrition assistant. Do not diagnose conditions or recommend dangerous starvation, dehydration, drugs, or training through serious pain."},
            {"role":"user","content":prompt.strip()},
        ], temperature=0.6, max_tokens=1800,
    )
    choices=getattr(result,"choices",None)
    answer=getattr(getattr(choices[0],"message",None),"content",None) if choices else None
    if not isinstance(answer,str) or not answer.strip():
        raise RuntimeError("AI service returned an empty response.")
    return answer.strip()


def error_json(message, status=400, key="response"):
    return jsonify({key: message}), status


def safe_ai_response(prompt, feature):
    try:
        return jsonify(response=ai_completion(prompt)), 200
    except ValueError as exc:
        return error_json(str(exc), 400)
    except Exception as exc:
        app.logger.exception("%s failed", feature)
        code=getattr(exc,"status_code",None)
        if code == 401: msg,status="AI credentials are invalid. Please contact the administrator.",503
        elif code == 403: msg,status="AI service denied the request. Check model access and account status.",503
        elif code == 404: msg,status="AI model not found. Check the GROQ_MODEL setting.",503
        elif code == 429: msg,status="AI service is busy. Please try again shortly.",429
        elif code in (408,504) or exc.__class__.__name__ in {"APITimeoutError","Timeout"}: msg,status="AI request timed out. Please try again.",504
        elif isinstance(exc,RuntimeError) and "not configured" in str(exc).lower(): msg,status="AI service is not configured. Please contact the administrator.",503
        else: msg,status="AI service is temporarily unavailable. Please try again later.",503
        return error_json(msg,status)


def safe_ai_response(prompt, feature):
    try:
        return jsonify(response=ai_completion(prompt)), 200
    except ValueError as exc:
        return error_json(str(exc), 400)
    except Exception as exc:
        app.logger.exception("%s failed", feature)
        code=getattr(exc,"status_code",None)
        if code == 401: msg,status="AI credentials are invalid. Please contact the administrator.",503
        elif code == 403: msg,status="AI service denied the request. Check model access and account status.",503
        elif code == 404: msg,status="AI model not found. Check the GROQ_MODEL setting.",503
        elif code == 429: msg,status="AI service is busy. Please try again shortly.",429
        elif code in (408,504) or exc.__class__.__name__ in {"APITimeoutError","Timeout"}: msg,status="AI request timed out. Please try again.",504
        elif isinstance(exc,RuntimeError) and "not configured" in str(exc).lower(): msg,status="AI service is not configured. Please contact the administrator.",503
        else: msg,status="AI service is temporarily unavailable. Please try again later.",503
        return error_json(msg,status)


def safe_ai_response(prompt, feature):
    try:
        return jsonify(response=ai_completion(prompt)), 200
    except ValueError as exc:
        return error_json(str(exc), 400)
    except Exception as exc:
        app.logger.exception("%s failed", feature)
        code=getattr(exc,"status_code",None)
        if code == 401: msg,status="AI credentials are invalid. Please contact the administrator.",503
        elif code == 403: msg,status="AI service denied the request. Check model access and account status.",503
        elif code == 404: msg,status="AI model not found. Check the GROQ_MODEL setting.",503
        elif code == 429: msg,status="AI service is busy. Please try again shortly.",429
        elif code in (408,504) or exc.__class__.__name__ in {"APITimeoutError","Timeout"}: msg,status="AI request timed out. Please try again.",504
        elif isinstance(exc,RuntimeError) and "not configured" in str(exc).lower(): msg,status="AI service is not configured. Please contact the administrator.",503
        else: msg,status="AI service is temporarily unavailable. Please try again later.",503
        return error_json(msg,status)


@app.route("/health")
def health():
    return jsonify({"status": "ok", "app": "MuscleMind-AI"})


@app.route("/")
def home():
    if not login_required():
        return redirect(url_for("login"))
    return render_template("index.html", username=session.get("username", "User"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    if not username or not email or len(password) < 8:
        return render_template("register.html", error="Enter your name and email, and use a password with at least 8 characters."), 400
    conn = connect_db()
    try:
        existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            return render_template("register.html", error="Email already exists. Please log in."), 409
        conn.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, generate_password_hash(password)),
        )
        conn.commit()
    finally:
        conn.close()
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html", google_enabled=google is not None)
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    conn = connect_db()
    try:
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    finally:
        conn.close()
    if user and user["password_hash"] and check_password_hash(user["password_hash"], password):
        session.clear()
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        return redirect(url_for("home"))
    return render_template("login.html", error="Invalid email or password.", google_enabled=google is not None), 401


@app.route("/google-login")
def google_login():
    if google is None:
        return "Google login is not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in environment variables.", 503
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI") or url_for("google_callback", _external=True)
    return google.authorize_redirect(redirect_uri)


@app.route("/google/callback")
def google_callback():
    if google is None:
        return redirect(url_for("login"))
    token = google.authorize_access_token()
    user_info = token.get("userinfo") or google.userinfo()
    email = (user_info.get("email") or "").strip().lower()
    if not email:
        return "Google did not provide an email address.", 400
    username = user_info.get("name") or email.split("@")[0]
    google_id = user_info.get("sub")
    picture = user_info.get("picture")
    conn = connect_db()
    try:
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if user is None:
            conn.execute(
                "INSERT INTO users (username, email, google_id, profile_pic) VALUES (?, ?, ?, ?)",
                (username, email, google_id, picture),
            )
            conn.commit()
            user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    finally:
        conn.close()
    session.clear()
    session["user_id"] = user["id"]
    session["username"] = user["username"]
    return redirect(url_for("home"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/workout")
def workout():
    if not login_required():
        return redirect(url_for("login"))
    return render_template("workout.html")


@app.route("/diet")
def diet():
    if not login_required():
        return redirect(url_for("login"))
    return render_template("diet.html")


@app.route("/chat")
def chat():
    if not login_required():
        return redirect(url_for("login"))
    return render_template("chat.html")


@app.route("/progress")
def progress():
    if not login_required():
        return redirect(url_for("login"))
    conn = connect_db()
    try:
        records = conn.execute(
            "SELECT * FROM progress WHERE user_id = ? ORDER BY id ASC", (session["user_id"],)
        ).fetchall()
    finally:
        conn.close()
    weights = [row["weight"] for row in records]
    waists = [row["waist"] for row in records]
    labels = [f"Entry {i + 1}" for i in range(len(records))]
    return render_template("progress.html", records=records, weights=weights, waists=waists, labels=labels)


@app.route("/generate_workout", methods=["POST"])
def generate_workout():
    if not login_required(): return error_json("Please log in first.",401)
    data=request.get_json(silent=True)
    if not isinstance(data,dict): return error_json("Send valid JSON workout details.",400)
    try: weight,height,days=float(data.get("weight")),float(data.get("height")),int(data.get("days"))
    except (TypeError,ValueError,OverflowError): return error_json("Weight, height and days must be valid numbers.",400)
    if not all(math.isfinite(x) for x in (weight,height)): return error_json("Weight and height must be finite numbers.",400)
    if not 20<=weight<=350: return error_json("Weight must be between 20 and 350 kg.",400)
    if not 3<=height<=8.5: return error_json("Height must be between 3 and 8.5 feet.",400)
    if not 1<=days<=7: return error_json("Training days must be between 1 and 7.",400)
    goal=str(data.get("goal","")).strip(); exp=str(data.get("experience","")).strip()
    if not goal or len(goal)>100 or not exp or len(exp)>100: return error_json("Enter a valid goal and experience level.",400)
    prompt=(f"Create a practical weekly gym plan. Weight: {weight:g} kg; height: {height:g} ft; goal: {goal}; experience: {exp}; training days: {days}. Include split, exercises, sets/reps, warm-up, recovery and safety tips. Do not recommend training through injury.")
    return safe_ai_response(prompt,"Workout generation")


@app.route("/generate_diet", methods=["POST"])
def generate_diet():
    if not login_required(): return error_json("Please log in first.",401)
    data=request.get_json(silent=True)
    if not isinstance(data,dict): return error_json("Send valid JSON diet details.",400)
    goal=str(data.get("goal","")).strip(); food=str(data.get("food","")).strip(); budget=str(data.get("budget","")).strip()
    try: meals=int(data.get("meals"))
    except (TypeError,ValueError,OverflowError): return error_json("Meals per day must be a number.",400)
    if not goal or len(goal)>100 or not food or len(food)>300 or not budget or len(budget)>100: return error_json("Enter a valid goal, food preference and budget.",400)
    if not 1<=meals<=8: return error_json("Meals per day must be between 1 and 8.",400)
    prompt=(f"Create a balanced practical meal plan. Goal: {goal}; food preference/restrictions: {food}; budget: {budget}; meals per day: {meals}. Include portions, protein sources, hydration and affordable alternatives. Respect allergies, avoid extreme restriction, and state that this is general information rather than medical advice.")
    return safe_ai_response(prompt,"Diet generation")


@app.route("/fitness_chat", methods=["POST"])
def fitness_chat():
    if not login_required(): return error_json("Please log in first.",401)
    data=request.get_json(silent=True)
    if not isinstance(data,dict): return error_json("Send your question as valid JSON.",400)
    message=data.get("message","")
    if not isinstance(message,str): return error_json("Your question must be text.",400)
    message=message.strip()
    if not message: return error_json("Enter a question first.",400)
    if len(message)>4000: return error_json("Question must be 4,000 characters or fewer.",400)
    return safe_ai_response(message,"Fitness chat")


@app.route("/save_progress", methods=["POST"])
def save_progress():
    if not login_required(): return error_json("Please log in first.",401,key="message")
    data=request.get_json(silent=True)
    if not isinstance(data,dict): return error_json("Send valid JSON progress details.",400,key="message")
    try:
        weight=float(data.get("weight")) if str(data.get("weight","")).strip() else None
        waist=float(data.get("waist")) if str(data.get("waist","")).strip() else None
    except (TypeError,ValueError,OverflowError): return error_json("Weight and waist must be numeric.",400,key="message")
    if weight is not None and (not math.isfinite(weight) or not 20<=weight<=350): return error_json("Weight must be between 20 and 350 kg.",400,key="message")
    if waist is not None and (not math.isfinite(waist) or not 20<=waist<=250): return error_json("Waist must be between 20 and 250 cm.",400,key="message")
    notes=str(data.get("notes","")).strip()
    if len(notes)>2000: return error_json("Notes must be 2,000 characters or fewer.",400,key="message")
    if weight is None and waist is None and not notes: return error_json("Enter weight, waist, or notes before saving.",400,key="message")
    conn=connect_db()
    try:
        conn.execute("INSERT INTO progress (user_id, weight, waist, notes) VALUES (?, ?, ?, ?)",(session["user_id"],weight,waist,notes)); conn.commit()
    except Exception:
        conn.rollback(); app.logger.exception("Saving progress failed")
        return error_json("Unable to save progress right now. Please try again.",500,key="message")
    finally: conn.close()
    return jsonify(message="Progress saved successfully!")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=os.getenv("FLASK_DEBUG") == "1")
