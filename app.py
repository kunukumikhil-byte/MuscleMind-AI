from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    redirect,
    session,
    url_for
)

from dotenv import load_dotenv
from groq import Groq
from database import create_tables, connect_db

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from authlib.integrations.flask_client import OAuth

import os


# ---------------- LOAD ENV ---------------- #

load_dotenv()


# ---------------- APP ---------------- #

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY")


# ---------------- DATABASE ---------------- #

create_tables()


# ---------------- GROQ ---------------- #

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


# ---------------- GOOGLE OAUTH ---------------- #

oauth = OAuth(app)

google = oauth.register(
    name="google",

    client_id=os.getenv(
        "GOOGLE_CLIENT_ID"
    ),

    client_secret=os.getenv(
        "GOOGLE_CLIENT_SECRET"
    ),

    server_metadata_url=
    "https://accounts.google.com/.well-known/openid-configuration",

    client_kwargs={
        "scope":
        "openid email profile"
    }
)


# ---------------- LOGIN CHECK ---------------- #

def login_required():

    if "user_id" not in session:
        return False

    return True


# ---------------- HOME ---------------- #

@app.route("/")
def home():

    if not login_required():
        return redirect("/login")

    return render_template(
        "index.html",
        username=session["username"]
    )


# ---------------- REGISTER ---------------- #

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if request.method == "POST":

        username = request.form[
            "username"
        ]

        email = request.form[
            "email"
        ]

        password = request.form[
            "password"
        ]

        hashed_password = (
            generate_password_hash(
                password
            )
        )

        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT *
        FROM users
        WHERE email = ?
        """, (email,))

        existing_user = (
            cursor.fetchone()
        )

        if existing_user:

            conn.close()

            return render_template(
                "register.html",
                error=
                "Email already exists"
            )

        cursor.execute("""
        INSERT INTO users
        (
            username,
            email,
            password_hash
        )
        VALUES (?, ?, ?)
        """, (
            username,
            email,
            hashed_password
        ))

        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template(
        "register.html"
    )


# ---------------- LOGIN ---------------- #

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        email = request.form[
            "email"
        ]

        password = request.form[
            "password"
        ]

        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT *
        FROM users
        WHERE email = ?
        """, (email,))

        user = (
            cursor.fetchone()
        )

        conn.close()

        if (
            user
            and
            check_password_hash(
                user[
                    "password_hash"
                ],
                password
            )
        ):

            session[
                "user_id"
            ] = user["id"]

            session[
                "username"
            ] = user[
                "username"
            ]

            return redirect("/")

        return render_template(
            "login.html",
            error=
            "Invalid credentials"
        )

    return render_template(
        "login.html"
    )


# ---------------- GOOGLE LOGIN ---------------- #

@app.route("/google-login")
def google_login():

    redirect_uri = (
        url_for(
            "google_callback",
            _external=True
        )
    )

    return google.authorize_redirect(
        redirect_uri
    )


# ---------------- GOOGLE CALLBACK ---------------- #

@app.route(
    "/google/callback"
)
def google_callback():

    token = (
        google.authorize_access_token()
    )

    user_info = (
        token["userinfo"]
    )

    email = (
        user_info["email"]
    )

    username = (
        user_info["name"]
    )

    google_id = (
        user_info["sub"]
    )

    picture = (
        user_info.get("picture")
    )

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT *
    FROM users
    WHERE email = ?
    """, (email,))

    user = cursor.fetchone()

    if not user:

        cursor.execute("""
        INSERT INTO users
        (
            username,
            email,
            google_id,
            profile_pic
        )
        VALUES (?, ?, ?, ?)
        """, (
            username,
            email,
            google_id,
            picture
        ))

        conn.commit()

        cursor.execute("""
        SELECT *
        FROM users
        WHERE email = ?
        """, (email,))

        user = cursor.fetchone()

    conn.close()

    session[
        "user_id"
    ] = user["id"]

    session[
        "username"
    ] = user[
        "username"
    ]

    return redirect("/")


# ---------------- LOGOUT ---------------- #

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")

# ---------------- WORKOUT PAGE ---------------- #

@app.route("/workout")
def workout():

    if not login_required():
        return redirect("/login")

    return render_template(
        "workout.html"
    )


# ---------------- DIET PAGE ---------------- #

@app.route("/diet")
def diet():

    if not login_required():
        return redirect("/login")

    return render_template(
        "diet.html"
    )


# ---------------- CHAT PAGE ---------------- #

@app.route("/chat")
def chat():

    if not login_required():
        return redirect("/login")

    return render_template(
        "chat.html"
    )


# ---------------- PROGRESS PAGE ---------------- #

@app.route("/progress")
def progress():

    if not login_required():
        return redirect("/login")

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM progress
        WHERE user_id = ?
        ORDER BY id ASC
    """, (
        session["user_id"],
    ))

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
        for i in range(
            len(records)
        )
    ]

    return render_template(
        "progress.html",
        records=records,
        weights=weights,
        waists=waists,
        labels=labels
    )


# ---------------- WORKOUT AI ---------------- #

@app.route(
    "/generate_workout",
    methods=["POST"]
)
def generate_workout():

    if not login_required():

        return jsonify({
            "response":
            "Please login first."
        })

    try:

        data = request.json

        prompt = f"""
        Create a professional
        gym workout plan.

        User Details:

        Weight:
        {data['weight']} kg

        Height:
        {data['height']} ft

        Goal:
        {data['goal']}

        Experience:
        {data['experience']}

        Workout Days:
        {data['days']}

        Generate:
        1. Weekly split
        2. Exercises
        3. Sets and reps
        4. Tips

        Format nicely.
        """

        response = (
            client.chat
            .completions.create(
                model=
                "llama-3.3-70b-versatile",

                messages=[
                    {
                        "role":
                        "user",

                        "content":
                        prompt
                    }
                ]
            )
        )

        result = (
            response
            .choices[0]
            .message
            .content
        )

        return jsonify({
            "response":
            result
        })

    except Exception as e:

        print(e)

        return jsonify({
            "response":
            f"Error: {str(e)}"
        })


# ---------------- DIET AI ---------------- #

@app.route(
    "/generate_diet",
    methods=["POST"]
)
def generate_diet():

    if not login_required():

        return jsonify({
            "response":
            "Please login first."
        })

    try:

        data = request.json

        prompt = f"""
        Create a healthy
        diet plan.

        Goal:
        {data['goal']}

        Food Preference:
        {data['food']}

        Budget:
        {data['budget']}

        Meals Per Day:
        {data['meals']}

        Include:
        - Calories
        - Protein
        - Carbs
        - Healthy meals

        Format nicely.
        """

        response = (
            client.chat
            .completions.create(
                model=
                "llama-3.3-70b-versatile",

                messages=[
                    {
                        "role":
                        "user",

                        "content":
                        prompt
                    }
                ]
            )
        )

        result = (
            response
            .choices[0]
            .message
            .content
        )

        return jsonify({
            "response":
            result
        })

    except Exception as e:

        print(e)

        return jsonify({
            "response":
            f"Error: {str(e)}"
        })


# ---------------- FITNESS CHAT ---------------- #

@app.route(
    "/fitness_chat",
    methods=["POST"]
)
def fitness_chat():

    if not login_required():

        return jsonify({
            "response":
            "Please login first."
        })

    try:

        message = request.json[
            "message"
        ]

        prompt = f"""
        You are MuscleMind AI,
        an expert fitness coach.

        Answer clearly
        and professionally.

        User Question:

        {message}
        """

        response = (
            client.chat
            .completions.create(
                model=
                "llama-3.3-70b-versatile",

                messages=[
                    {
                        "role":
                        "user",

                        "content":
                        prompt
                    }
                ]
            )
        )

        result = (
            response
            .choices[0]
            .message
            .content
        )

        return jsonify({
            "response":
            result
        })

    except Exception as e:

        print(e)

        return jsonify({
            "response":
            f"Error: {str(e)}"
        })
        
# ---------------- SAVE PROGRESS ---------------- #

@app.route(
    "/save_progress",
    methods=["POST"]
)
def save_progress():

    if not login_required():

        return jsonify({
            "message":
            "Please login first."
        })

    try:

        data = request.json

        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO progress
        (
            user_id,
            weight,
            waist,
            notes
        )
        VALUES (?, ?, ?, ?)
        """, (

            session["user_id"],

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

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )