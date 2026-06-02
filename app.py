from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from groq import Groq
from database import create_tables, connect_db
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# Create DB tables
create_tables()

# Groq Client
client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


# ---------------- HOME ---------------- #

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

    cursor.execute("""
        SELECT *
        FROM progress
        ORDER BY id ASC
    """)

    records = cursor.fetchall()

    conn.close()

    weights = [
        row["weight"]
        for row in records
    ]

    waists = [
        row["waist"]
        for row in records
    ]

    labels = [
        f"Entry {i+1}"
        for i in range(len(records))
    ]

    return render_template(
        "progress.html",
        records=records,
        weights=weights,
        waists=waists,
        labels=labels
    )


# ---------------- WORKOUT AI ---------------- #

@app.route("/generate_workout", methods=["POST"])
def generate_workout():

    try:
        data = request.json

        prompt = f"""
        Create a professional gym workout plan.

        User Details:
        Weight: {data['weight']} kg
        Height: {data['height']} ft
        Goal: {data['goal']}
        Experience: {data['experience']}
        Workout Days: {data['days']}

        Generate:
        1. Weekly split
        2. Exercises
        3. Sets and reps
        4. Tips

        Format nicely.
        """

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",

            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        result = (
            response
            .choices[0]
            .message
            .content
        )

        return jsonify({
            "response": result
        })

    except Exception as e:

        print(e)

        return jsonify({
            "response":
            f"Error: {str(e)}"
        })


# ---------------- DIET AI ---------------- #

@app.route("/generate_diet", methods=["POST"])
def generate_diet():

    try:
        data = request.json

        prompt = f"""
        Create a healthy diet plan.

        Goal: {data['goal']}
        Food Preference: {data['food']}
        Budget: {data['budget']}
        Meals Per Day: {data['meals']}

        Include:
        - Calories
        - Protein
        - Carbs
        - Healthy meals

        Format nicely.
        """

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",

            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        result = (
            response
            .choices[0]
            .message
            .content
        )

        return jsonify({
            "response": result
        })

    except Exception as e:

        print(e)

        return jsonify({
            "response":
            f"Error: {str(e)}"
        })


# ---------------- FITNESS CHAT ---------------- #

@app.route("/fitness_chat", methods=["POST"])
def fitness_chat():

    try:
        message = request.json["message"]

        prompt = f"""
        You are MuscleMind AI,
        an expert fitness coach.

        Answer clearly and professionally.

        User Question:
        {message}
        """

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",

            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        result = (
            response
            .choices[0]
            .message
            .content
        )

        return jsonify({
            "response": result
        })

    except Exception as e:

        print(e)

        return jsonify({
            "response":
            f"Error: {str(e)}"
        })


# ---------------- SAVE PROGRESS ---------------- #

@app.route("/save_progress", methods=["POST"])
def save_progress():

    try:
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
            "message":
            "Progress saved successfully!"
        })

    except Exception as e:

        print(e)

        return jsonify({
            "message":
            f"Error: {str(e)}"
        })


# ---------------- RUN APP ---------------- #

if __name__ == "__main__":
    app.run(debug=True)