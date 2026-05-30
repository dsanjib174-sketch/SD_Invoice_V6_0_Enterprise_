from flask import Blueprint, render_template, request, redirect, session, Response, url_for, flash, current_app
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import os, json, uuid
from datetime import datetime

auth_bp = Blueprint("auth", __name__)

USERS_FILE = "users.json"


def _users_path():
    return os.path.join(current_app.config["UPLOAD_FOLDER"], USERS_FILE)


def load_users():
    path = _users_path()
    if not os.path.exists(path):
        default_users = [
            {
                "id": uuid.uuid4().hex,
                "name": "Super Admin",
                "email": "superadmin@sdinvoice.com",
                "user_id": "superadmin@sdinvoice.com",
                "password": generate_password_hash("Admin@123"),
                "role": "superadmin",
                "branch": "All Branches",
                "status": "Active",
                "created_at": datetime.now().strftime("%d-%m-%Y %I:%M %p")
            }
        ]
        save_users(default_users)
        return default_users

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_users(items):
    os.makedirs(os.path.dirname(_users_path()), exist_ok=True)
    with open(_users_path(), "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)


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


def authenticate_user(user_id, password, required_role=None):
    users = load_users()

    for u in users:
        if u.get("status") != "Active":
            continue

        if u.get("user_id") == user_id or u.get("email") == user_id:
            if required_role and u.get("role") != required_role:
                return None

            stored_password = u.get("password", "")

            if stored_password.startswith("pbkdf2:") or stored_password.startswith("scrypt:"):
                if check_password_hash(stored_password, password):
                    return u
            else:
                if stored_password == password:
                    return u

    return None


@auth_bp.route("/", methods=["GET", "POST", "HEAD"])
def client_login():
    if request.method == "HEAD":
        return Response(status=200)

    if request.method == "POST":
        user_id = request.form.get("user_id", "").strip()
        password = request.form.get("password", "").strip()

        user = authenticate_user(user_id, password)

        if user and user.get("role") != "superadmin":
            session["login_type"] = "client"
            session["user"] = user.get("email")
            session["user_id"] = user.get("user_id")
            session["user_name"] = user.get("name")
            session["role"] = user.get("role")
            session["branch"] = user.get("branch")
            session["client_name"] = user.get("company", "Client")
            return redirect("/dashboard")

        flash("Invalid client login ID or password.", "error")

    return render_template("auth/client_login.html", login_mode="Client Login")


@auth_bp.route("/admin", methods=["GET", "POST", "HEAD"])
def admin_login():
    if request.method == "HEAD":
        return Response(status=200)

    if request.method == "POST":
        user_id = request.form.get("user_id", "").strip()
        password = request.form.get("password", "").strip()

        user = authenticate_user(user_id, password, required_role="superadmin")

        if user:
            session["login_type"] = "superadmin"
            session["user"] = user.get("email")
            session["user_id"] = user.get("user_id")
            session["user_name"] = user.get("name")
            session["role"] = "superadmin"
            session["branch"] = "All Branches"
            session["client_name"] = "All Clients"
            return redirect("/dashboard")

        flash("Invalid Super Admin login ID or password.", "error")

    return render_template("auth/client_login.html", login_mode="Super Admin Login", admin=True)


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@auth_bp.route("/forgot-password")
def forgot_password():
    return render_template("auth/forgot_password.html")
