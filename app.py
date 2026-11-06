import os

from dotenv import load_dotenv
load_dotenv()

from flask import (
    Flask, render_template, request,
    redirect, url_for, flash, session
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from mysql.connector import Error, IntegrityError

from database.db import get_db_connection


app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

if not app.secret_key:
    raise RuntimeError("SECRET_KEY was not loaded from the .env file.")




@app.route("/")
def home():
    return render_template("index.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        # Retrieve submitted form data
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        # Validate submitted data
        if not username or not password:
            flash("Please complete all fields.", "error")
            return redirect(url_for("signup"))

        if len(username) > 50:
            flash("Username cannot exceed 50 characters.", "error")
            return redirect(url_for("signup"))

        if len(password) < 8:
            flash("Password must contain at least 8 characters.", "error")
            return redirect(url_for("signup"))

        connection = None
        cursor = None

        try:
            # Establish database connection
            connection = get_db_connection()
            cursor = connection.cursor()

            # Check whether username already exists
            cursor.execute(
                "SELECT id FROM tbl_user WHERE username = %s",
                (username,)
            )

            existing_user = cursor.fetchone()

            if existing_user:
                flash("That username is already taken.", "error")
                return redirect(url_for("signup"))

            # Hash the password
            hashed_password = generate_password_hash(password)

            # Insert new user
            cursor.execute(
                """
                INSERT INTO tbl_user (username, password)
                VALUES (%s, %s)
                """,
                (username, hashed_password)
            )

            connection.commit()

            flash("Account created successfully. You can now sign in.", "success")
            return redirect(url_for("login"))

        except IntegrityError:
            if connection:
                connection.rollback()

            flash("That username is already taken.", "error")
            return redirect(url_for("signup"))

        except Error:
            if connection:
                connection.rollback()

            app.logger.exception("Database error during registration.")
            flash("Registration failed. Please try again later.", "error")
            return redirect(url_for("signup"))

        finally:
            if cursor:
                cursor.close()

            if connection and connection.is_connected():
                connection.close()

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Please enter your username and password.", "error")
            return redirect(url_for("login"))

        connection = None
        cursor = None

        try:
            # Connect to the database
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)

            # Retrieve the user
            cursor.execute(
                "SELECT id, username, password FROM tbl_user WHERE username = %s",
                (username,)
            )

            user = cursor.fetchone()

            # Verify credentials
            if user and check_password_hash(user["password"], password):

                session["user_id"] = user["id"]
                session["username"] = user["username"]

                flash("Login successful. Welcome back!", "success")

                return redirect(url_for("dashboard"))

            flash("Invalid username or password.", "error")
            return redirect(url_for("login"))

        except Error:
            app.logger.exception("Database error during login.")
            flash("Something went wrong. Please try again.", "error")
            return redirect(url_for("login"))

        finally:
            if cursor:
                cursor.close()

            if connection and connection.is_connected():
                connection.close()

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        flash("Please log in to access your dashboard.", "error")
        return redirect(url_for("login"))

    return render_template("dashboard.html")

@app.route("/logout")
def logout():

    session.clear()

    flash("You have been logged out successfully.", "success")

    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)