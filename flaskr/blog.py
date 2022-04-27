import flask
from flask import Blueprint
from werkzeug import exceptions

from . import auth, database

bp = Blueprint("blog", __name__)


@bp.route("/")
def index():
    db = database.get_db()
    posts = db.execute(
        "SELECT p.id, title, body, created, author_id, username"
        " FROM post p JOIN user u ON p.author_id = u.id"
        " ORDER BY created DESC"
    ).fetchall()
    return flask.render_template("blog/index.html", posts=posts)


@bp.route("/create", methods=("GET", "POST"))
@auth.login_required
def create():
    if flask.request.method == "POST":
        title = flask.request.form["title"]
        body = flask.request.form["body"]
        error = None

        if not title:
            error = "Title is required."

        if error is not None:
            flask.flash(error)
        else:
            db = database.get_db()
            db.execute(
                "INSERT INTO post (title, body, author_id)" " VALUES (?, ?, ?)",
                (title, body, flask.g.user["id"]),
            )
            db.commit()
            return flask.redirect(flask.url_for("blog.index"))

    return flask.render_template("blog/create.html")


def get_post(id, check_author=True):
    post = (
        database.get_db()
        .execute(
            "SELECT p.id, title, body, created, author_id, username"
            " FROM post p JOIN user u ON p.author_id = u.id"
            " WHERE p.id = ?",
            (id,),
        )
        .fetchone()
    )

    if post is None:
        exceptions.abort(404, f"Post id {id} doesn't exist.")

    if check_author and post["author_id"] != flask.g.user["id"]:
        exceptions.abort(403)

    return post


@bp.route("/<int:id>/update", methods=("GET", "POST"))
@auth.login_required
def update(id):
    post = get_post(id)

    if flask.request.method == "POST":
        title = flask.request.form["title"]
        body = flask.request.form["body"]
        error = None

        if not title:
            error = "Title is required."

        if error is not None:
            flask.flash(error)
        else:
            db = database.get_db()
            db.execute(
                "UPDATE post SET title = ?, body = ?" " WHERE id = ?", (title, body, id)
            )
            db.commit()
            return flask.redirect(flask.url_for("blog.index"))

    return flask.render_template("blog/update.html", post=post)


@bp.route("/<int:id>/delete", methods=("POST",))
@auth.login_required
def delete(id):
    get_post(id)
    db = database.get_db()
    db.execute("DELETE FROM post WHERE id = ?", (id,))
    db.commit()
    return flask.redirect(flask.url_for("blog.index"))
