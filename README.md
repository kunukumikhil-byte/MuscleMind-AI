# MuscleMind AI

MuscleMind AI is a Flask fitness application with workout generation, diet planning, fitness chat, account login, optional Google OAuth, and progress tracking.

## Features

- User registration and login
- AI workout-plan generation using Groq
- AI diet-plan generation using Groq
- Fitness Q&A chat
- Weight and waist progress tracking with charts
- Optional Google OAuth sign-in
- Responsive HTML/CSS/JavaScript frontend

## Stack

- Python + Flask
- SQLite for local development
- Groq API for AI features
- Authlib for optional Google OAuth
- Chart.js for progress charts

## Run locally

1. Install Python 3.11 or newer.
2. Create and activate a virtual environment.
3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Copy `.env.example` to `.env` and set `GROQ_API_KEY` and a strong `SECRET_KEY`.
5. Run the app:

   ```bash
   python app.py
   ```

6. Open `http://127.0.0.1:5000`.

Google sign-in is optional. Set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` only if configuring Google OAuth; add the deployed callback URL `/google/callback` to your Google OAuth client's authorized redirect URIs.

## Deploy to Vercel

1. Push the project root to GitHub. `app.py`, `database.py`, `requirements.txt`, `vercel.json`, `templates/`, and `static/` must be in the configured Vercel Root Directory.
2. Import the repository into Vercel and deploy.
3. In **Project Settings → Environment Variables**, add:
   - `GROQ_API_KEY` — required for AI features
   - `SECRET_KEY` — a long, random secret value
   - `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` — optional, only if using Google sign-in
4. Redeploy after changing environment variables.
5. Visit `/health` to confirm the Flask function responds.

The `vercel.json` file explicitly configures the Python function and includes the templates, static assets, and database helper.

## Important database note

The app uses SQLite for local development. On Vercel, the database is placed in `/tmp` because the serverless filesystem is ephemeral. This can work for a temporary demo, but data may disappear between instances or deployments and should not be treated as persistent. For real user accounts and progress history, connect a managed persistent database (for example, PostgreSQL) and adapt the database layer before production use.

## Environment variables

See `.env.example`. Never commit `.env` or API keys to GitHub.

## Developer

Mikhil Kunuku
