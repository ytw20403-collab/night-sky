from flask import Flask, render_template, request, jsonify, session, redirect
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "night-sky-secret-key"
)

DB = "sky.db"

PASSWORD = os.environ.get(
    "DASHBOARD_PASSWORD",
    "night-sky-1234"
)


def init_db():
    conn = sqlite3.connect(DB)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            accuracy REAL,
            created_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/save-location", methods=["POST"])
def save_location():

    data = request.get_json(silent=True)

    if not data:
        return jsonify({"success": False}), 400

    latitude = data.get("latitude")
    longitude = data.get("longitude")
    accuracy = data.get("accuracy")

    if latitude is None or longitude is None:
        return jsonify({"success": False}), 400

    try:
        latitude = float(latitude)
        longitude = float(longitude)

        if accuracy is not None:
            accuracy = float(accuracy)

    except (TypeError, ValueError):
        return jsonify({"success": False}), 400

    conn = sqlite3.connect(DB)

    conn.execute("""
        INSERT INTO locations
        (latitude, longitude, accuracy, created_at)
        VALUES (?, ?, ?, ?)
    """, (
        latitude,
        longitude,
        accuracy,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()

    return jsonify({"success": True})


@app.route("/dashboard", methods=["GET"])
def dashboard():

    if not session.get("dashboard_logged_in"):
        return redirect("/dashboard-login")

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    locations = conn.execute("""
        SELECT id, latitude, longitude, accuracy, created_at
        FROM locations
        ORDER BY id DESC
        LIMIT 3
    """).fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        locations=locations
    )


@app.route("/dashboard-login", methods=["GET", "POST"])
def dashboard_login():

    error = None

    if request.method == "POST":

        password = request.form.get("password", "")

        if password == PASSWORD:

            session["dashboard_logged_in"] = True

            return redirect("/dashboard")

        error = "Wrong password"

    return render_template(
        "login.html",
        error=error
    )


@app.route("/dashboard-logout")
def dashboard_logout():

    session.clear()

    return redirect("/dashboard-login")


init_db()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8080,
        debug=False
    )
