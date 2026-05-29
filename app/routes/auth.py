from flask import Blueprint, render_template, request, redirect, session, Response, url_for, flash
from functools import wraps

auth_bp = Blueprint("auth", __name__)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("login_type"):
            return redirect(url_for("auth.client_login"))
        return view(*args, **kwargs)
    return wrapped


def superadmin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("login_type") != "superadmin":
            flash("Super Admin access required.", "error")
            return redirect(url_for("dashboard.dashboard"))
        return view(*args, **kwargs)
    return wrapped


@auth_bp.route("/", methods=["GET", "POST", "HEAD"])
def client_login():
    if request.method == "HEAD":
        return Response(status=200)
    if request.method == "POST":
        session["login_type"] = "client"
        session["user"] = request.form.get("user_id", "client")
        session["client_name"] = request.form.get("client_name", "Demo Client")
        return redirect("/dashboard")
    return render_template("auth/client_login.html", login_mode="Client Login")


@auth_bp.route("/admin", methods=["GET", "POST", "HEAD"])
def admin_login():
    if request.method == "HEAD":
        return Response(status=200)
    if request.method == "POST":
        session["login_type"] = "superadmin"
        session["user"] = request.form.get("user_id", "superadmin")
        session["client_name"] = "All Clients"
        return redirect("/dashboard")
    return render_template("auth/client_login.html", login_mode="Super Admin Login", admin=True)


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@auth_bp.route("/forgot-password")
def forgot_password():
    return render_template("auth/forgot_password.html")
