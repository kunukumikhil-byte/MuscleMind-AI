from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import google.generativeai as genai
import os
from database import create_tables, connect_db

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

create_tables()

# Gemini API setup
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-1.5-flash")


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/workout")
def workout():
    return render_template("workout.html")


@app.route("/diet")
def diet():
    return render_template("diet.html")


@app.route("/chat")
def chat():
    return render_template("chat.html")


@app.route("/progress")
def progress():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM progress")
    records = cursor.fetchall()

    conn.close()

    return render_template(
        "progress.html",
        records=records
    )


@app.route("/generate_workout", methods=["POST"])
def generate_workout():
    data = request.json

    prompt = f"""
    Create a gym workout plan.

    Weight: {data['weight']} kg
    Height: {data['height']} ft
    Goal: {data['goal']}
    Experience: {data['experience']}
    Days per week: {data['days']}

    Give workout split,
    exercises,
    sets and reps.
    """

    response = model.generate_content(prompt)

    return jsonify({
        "response": response.text
    })


@app.route("/generate_diet", methods=["POST"])
def generate_diet():
    data = request.json

    prompt = f"""
    Create a healthy diet plan.

    Goal: {data['goal']}
    Food Preference: {data['food']}
    Budget: {data['budget']}
    Meals Per Day: {data['meals']}

    Include calories,
    protein,
    carbs,
    and healthy meal suggestions.
    """

    response = model.generate_content(prompt)

    return jsonify({
        "response": response.text
    })


@app.route("/fitness_chat", methods=["POST"])
def fitness_chat():
    message = request.json["message"]

    prompt = f"""
    You are MuscleMind AI,
    a professional gym and fitness coach.

    User Question:
    {message}
    """

    response = model.generate_content(prompt)

    return jsonify({
        "response": response.text
    })


@app.route("/save_progress", methods=["POST"])
def save_progress():
    data = request.json

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO progress
    (weight, waist, notes)
    VALUES (?, ?, ?)
    """, (
        data["weight"],
        data["waist"],
        data["notes"]
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Progress saved"
    })


if __name__ == "__main__":
    app.run(debug=True)