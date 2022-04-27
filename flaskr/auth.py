import functools

import flask
from flask import Blueprint
from werkzeug import security

from flaskr import database

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/sign-up", methods=("GET", "POST"))
def sign_up():
    if flask.request.method == "POST":
        username = flask.request.form["username"]
        password = flask.request.form["password"]
        db = database.get_db()
        error = None

        if not username:
            error = "Username is required."
        elif not password:
            error = "Password is required."

        if error is None:
            try:
                db.execute(
                    "INSERT INTO user (username, password) VALUES (?, ?)",
                    (username, security.generate_password_hash(password)),
                )
                db.commit()
            except db.IntegrityError:
                error = f"User {username} is already registered."
            else:
                return flask.redirect(flask.url_for("auth.login"))

        flask.flash(error)

    return flask.render_template("auth/sign_up.html")


@bp.route("/login", methods=("GET", "POST"))
def login():
    if flask.request.method == "POST":
        username = flask.request.form["username"]
        password = flask.request.form["password"]
        db = database.get_db()
        error = None
        user = db.execute(
            "SELECT * FROM user WHERE username = ?", (username,)
        ).fetchone()

        print(user)

        if user is None:
            error = "Incorrect username."
        elif not security.check_password_hash(user["password"], password):
            error = "Incorrect password."

        if error is None:
            flask.session.clear()
            flask.session["user_id"] = user["id"]
            return flask.redirect(flask.url_for("index"))

        flask.flash(error)

    return flask.render_template("auth/login.html")


@bp.route("/logout")
def logout():
    flask.session.clear()
    return flask.redirect(flask.url_for("index"))


@bp.before_app_request
def load_logged_in_user():
    user_id = flask.session.get("user_id")

    if user_id is None:
        flask.g.user = None
    else:
        flask.g.user = (
            database.get_db().execute("SELECT * FROM user WHERE id = ?", (user_id,))
        ).fetchone()


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if flask.g.user is None:
            return flask.redirect(flask.url_for("auth.login"))

        return view(**kwargs)

    return wrapped_view
