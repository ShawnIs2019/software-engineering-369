"""Campus Event Management System (CEMS) - application factory."""
import os

from flask import Flask, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(
        # Set SECRET_KEY in the environment for real deployments.
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-only-change-me"),
        # SQLite for local development. For PostgreSQL set DATABASE_URL, e.g.
        # postgresql://user:password@localhost/cems
        SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URL", "sqlite:///cems.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    if test_config:
        app.config.update(test_config)

    db.init_app(app)

    from cems import models  # noqa: F401  (registers the User table)
    from cems.auth import auth_bp

    app.register_blueprint(auth_bp)

    with app.app_context():
        db.create_all()

    @app.route("/")
    def index():
        if session.get("user_id") is not None:
            return redirect(url_for("auth.dashboard"))
        return redirect(url_for("auth.login"))

    return app
