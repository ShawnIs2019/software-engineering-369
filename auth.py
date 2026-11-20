"""Registration, login, logout and a protected dashboard page."""
import re
from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from cems import db
from cems.models import STUDENT, User

auth_bp = Blueprint("auth", __name__)

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD_LENGTH = 8


def login_required(view):
    """Redirect to the login page if nobody is logged in."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("user_id") is None:
            flash("Please log in to continue.", "error")
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)
    return wrapped


def validate_registration(name, email, password, confirm_password):
    errors = []
    if not name:
        errors.append("Name is required.")
    if not EMAIL_PATTERN.match(email):
        errors.append("Enter a valid email address.")
    if len(password) < MIN_PASSWORD_LENGTH:
        errors.append(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
    if password != confirm_password:
        errors.append("Passwords do not match.")
    return errors


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        errors = validate_registration(name, email, password, confirm_password)
        if not errors and User.query.filter_by(email=email).first():
            errors.append("An account with that email already exists.")

        if errors:
            for message in errors:
                flash(message, "error")
            return render_template("register.html", name=name, email=email), 400

        # Self-registration always creates a Student. Organizer and Admin
        # roles are granted later by an admin (a separate user story).
        user = User(name=name, email=email, role=STUDENT)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash("Account created. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()
        if user is None or not user.check_password(password):
            # Same message for both cases so attackers cannot tell which emails exist.
            flash("Invalid email or password.", "error")
            return render_template("login.html", email=email), 401

        session.clear()
        session["user_id"] = user.id
        session["role"] = user.role
        return redirect(url_for("auth.dashboard"))

    return render_template("login.html")


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.login"))


@auth_bp.route("/dashboard")
@login_required
def dashboard():
    user = db.session.get(User, session["user_id"])
    if user is None:  # account was deleted while logged in
        session.clear()
        return redirect(url_for("auth.login"))
    return render_template("dashboard.html", user=user)
