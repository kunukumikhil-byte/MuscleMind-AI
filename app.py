"""MuscleMind-AI Flask application, configured for Vercel Python functions."""
import os
from functools import wraps

from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database import connect_db, create_tables

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY") or "development-only-change-this-secret"
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
    response = get_groq_client().chat.completions.create(
        model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        messages=[
            {"role": "system", "content": "You are MuscleMind AI, a helpful fitness and nutrition assistant. Give practical, safety-conscious guidance. Do not diagnose medical conditions."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.6,
    )
    return response.choices[0].message.content or "No response was generated."


def error_json(message, status=400, key="response"):
    return jsonify({key: message}), status


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
    redirect_uri = url_for("google_callback", _external=True)
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
    if not login_required():
        return error_json("Please log in first.", 401)
    data = request.get_json(silent=True) or {}
    required = ("weight", "height", "goal", "experience", "days")
    if any(not str(data.get(k, "")).strip() for k in required):
        return error_json("Please complete all workout fields.")
    prompt = f"""Create a practical weekly gym workout plan.
Weight: {data['weight']} kg
Height: {data['height']} ft
Goal: {data['goal']}
Experience: {data['experience']}
Workout days per week: {data['days']}
Include a weekly split, exercises, sets/reps, warm-up, recovery and safety tips. Keep it appropriate to the stated experience level."""
    try:
        return jsonify(response=ai_completion(prompt))
    except Exception as exc:
        app.logger.exception("Workout generation failed")
        return error_json(str(exc), 503)


@app.route("/generate_diet", methods=["POST"])
def generate_diet():
    if not login_required():
        return error_json("Please log in first.", 401)
    data = request.get_json(silent=True) or {}
    required = ("goal", "food", "budget", "meals")
    if any(not str(data.get(k, "")).strip() for k in required):
        return error_json("Please complete all diet fields.")
    prompt = f"""Create a balanced, practical meal plan.
Goal: {data['goal']}
Food preference: {data['food']}
Budget: {data['budget']}
Meals per day: {data['meals']}
Include meal suggestions, approximate portions, protein sources, hydration and affordable substitutions. Avoid claiming this is medical advice. State assumptions when calorie or body details are unavailable."""
    try:
        return jsonify(response=ai_completion(prompt))
    except Exception as exc:
        app.logger.exception("Diet generation failed")
        return error_json(str(exc), 503)


@app.route("/fitness_chat", methods=["POST"])
def fitness_chat():
    if not login_required():
        return error_json("Please log in first.", 401)
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()
    if not message:
        return error_json("Enter a question first.")
    try:
        return jsonify(response=ai_completion(message))
    except Exception as exc:
        app.logger.exception("Fitness chat failed")
        return error_json(str(exc), 503)


@app.route("/save_progress", methods=["POST"])
def save_progress():
    if not login_required():
        return error_json("Please log in first.", 401, key="message")
    data = request.get_json(silent=True) or {}
    try:
        weight = float(data.get("weight")) if str(data.get("weight", "")).strip() else None
        waist = float(data.get("waist")) if str(data.get("waist", "")).strip() else None
    except (TypeError, ValueError):
        return error_json("Weight and waist must be numeric values.", key="message")
    notes = str(data.get("notes", "")).strip()[:2000]
    if weight is None and waist is None and not notes:
        return error_json("Enter weight, waist, or notes before saving.", key="message")
    conn = connect_db()
    try:
        conn.execute(
            "INSERT INTO progress (user_id, weight, waist, notes) VALUES (?, ?, ?, ?)",
            (session["user_id"], weight, waist, notes),
        )
        conn.commit()
    finally:
        conn.close()
    return jsonify(message="Progress saved successfully!")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=os.getenv("FLASK_DEBUG") == "1")
