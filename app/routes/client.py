from flask import Blueprint, render_template
from .auth import login_required
client_bp = Blueprint("client", __name__)
@client_bp.route("/company-profile")
@login_required
def company_profile(): return render_template("client/company_profile.html")
@client_bp.route("/branches")
@login_required
def branches(): return render_template("client/branches.html")
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session
from werkzeug.security import generate_password_hash
from .auth import login_required
import os, json, uuid
from datetime import datetime

client_bp = Blueprint("client", __name__)

USERS_FILE = "users.json"
BRANCHES_FILE = "branches.json"


def _json_path(filename):
    return os.path.join(current_app.config["UPLOAD_FOLDER"], filename)


def load_json(filename, default_value):
    path = _json_path(filename)
    if not os.path.exists(path):
        return default_value
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(filename, items):
    os.makedirs(os.path.dirname(_json_path(filename)), exist_ok=True)
    with open(_json_path(filename), "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)


def load_users():
    return load_json(USERS_FILE, [])


def save_users(items):
    save_json(USERS_FILE, items)


def load_branches():
    branches = load_json(BRANCHES_FILE, [])

    if not branches:
        branches = [
            {"id": uuid.uuid4().hex, "branch_name": "Main Branch", "branch_code": "MAIN"}
        ]
        save_json(BRANCHES_FILE, branches)

    return branches


@client_bp.route("/company-profile")
@login_required
def company_profile():
    return render_template("client/company_profile.html")


@client_bp.route("/branches")
@login_required
def branches():
    return render_template("client/branches.html")


@client_bp.route("/users", methods=["GET", "POST"])
@login_required
def users():
    users_data = load_users()
    branches_data = load_branches()

    if request.method == "POST":
        action = request.form.get("action")

        if action == "add":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip()
            user_id = request.form.get("user_id", "").strip()
            password = request.form.get("password", "").strip()
            role = request.form.get("role", "client").strip()
            branch = request.form.get("branch", "").strip()
            status = request.form.get("status", "Active").strip()

            if not name or not email or not user_id or not password:
                flash("Name, Email, User ID and Password are required.", "error")
                return redirect(url_for("client.users"))

            for u in users_data:
                if u.get("user_id") == user_id or u.get("email") == email:
                    flash("User ID or Email already exists.", "error")
                    return redirect(url_for("client.users"))

            if session.get("login_type") != "superadmin":
                role = "client"

            users_data.insert(0, {
                "id": uuid.uuid4().hex,
                "name": name,
                "email": email,
                "user_id": user_id,
                "password": generate_password_hash(password),
                "role": role,
                "branch": branch,
                "status": status,
                "created_by": session.get("user", ""),
                "created_at": datetime.now().strftime("%d-%m-%Y %I:%M %p")
            })

            save_users(users_data)
            flash("User added successfully.", "success")

        elif action == "update":
            user_record_id = request.form.get("user_record_id")
            new_password = request.form.get("password", "").strip()

            for u in users_data:
                if u.get("id") == user_record_id:
                    u["name"] = request.form.get("name", "").strip()
                    u["email"] = request.form.get("email", "").strip()
                    u["user_id"] = request.form.get("user_id", "").strip()
                    u["branch"] = request.form.get("branch", "").strip()
                    u["status"] = request.form.get("status", "Active").strip()

                    if session.get("login_type") == "superadmin":
                        u["role"] = request.form.get("role", "client").strip()

                    if new_password:
                        u["password"] = generate_password_hash(new_password)

                    u["updated_at"] = datetime.now().strftime("%d-%m-%Y %I:%M %p")
                    break

            save_users(users_data)
            flash("User updated successfully.", "success")

        return redirect(url_for("client.users"))

    return render_template(
        "client/users.html",
        users=users_data,
        branches=branches_data
    )





@client_bp.route("/communication")
@login_required
def communication():
    return render_template("client/communication.html")
@client_bp.route("/change-password")
@login_required
def change_password(): return render_template("client/change_password.html")
@client_bp.route("/communication")
@login_required
def communication(): return render_template("client/communication.html")
