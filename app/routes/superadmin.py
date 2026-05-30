from flask import Blueprint, render_template, request, redirect, url_for, current_app, flash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os, json, uuid
from .auth import login_required, superadmin_required

superadmin_bp = Blueprint("superadmin", __name__)

DATA_FILE = "updates.json"
CLIENTS_FILE = "clients.json"

ALLOWED_EXT = {"png", "jpg", "jpeg", "gif", "webp"}

PLANS = {
    "Basic": 1,
    "Standard": 1,
    "Premium": 1,
    "Enterprise": 1
}


def _data_path():
    return os.path.join(current_app.config["UPLOAD_FOLDER"], DATA_FILE)


def _clients_path():
    return os.path.join(current_app.config["UPLOAD_FOLDER"], CLIENTS_FILE)


def load_updates():
    path = _data_path()
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_updates(items):
    with open(_data_path(), "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)


def load_clients():
    path = _clients_path()
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_clients(items):
    with open(_clients_path(), "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)


@superadmin_bp.route("/superadmin/clients", methods=["GET", "POST"])
@login_required
@superadmin_required
def clients():
    if request.method == "POST":
        action = request.form.get("action")
        clients_data = load_clients()

        if action == "create":
            company = request.form.get("company", "").strip()
            email = request.form.get("email", "").strip()
            user_limit = request.form.get("user_limit", "").strip()
            branch_limit = request.form.get("branch_limit", "").strip()
            plan_name = request.form.get("plan_name", "").strip()

            active_date = datetime.today().date()
            expire_date = active_date + timedelta(days=365)

            if company and email and plan_name:
                clients_data.insert(0, {
                    "id": uuid.uuid4().hex,
                    "company": company,
                    "email": email,
                    "user_limit": user_limit,
                    "branch_limit": branch_limit,
                    "plan_name": plan_name,
                    "active_date": active_date.strftime("%Y-%m-%d"),
                    "expire_date": expire_date.strftime("%Y-%m-%d"),
                    "expiry_edit_comment": "",
                    "status": "Active",
                    "created_at": datetime.now().strftime("%d-%m-%Y %I:%M %p")
                })

                save_clients(clients_data)
                flash("Client created successfully.", "success")
            else:
                flash("Company, Email and Plan Name are required.", "error")

        elif action == "edit_expiry":
            client_id = request.form.get("client_id")
            new_expire_date = request.form.get("new_expire_date")
            comment = request.form.get("comment", "").strip()

            if not new_expire_date:
                flash("New expiry date is required.", "error")
                return redirect(url_for("superadmin.clients"))

            if not comment:
                flash("Valid comment is required to edit expiry date.", "error")
                return redirect(url_for("superadmin.clients"))

            updated = False

            for c in clients_data:
                if c.get("id") == client_id:
                    c["expire_date"] = new_expire_date
                    c["expiry_edit_comment"] = comment
                    c["expiry_updated_at"] = datetime.now().strftime("%d-%m-%Y %I:%M %p")
                    updated = True
                    break

            if updated:
                save_clients(clients_data)
                flash("Expiry date updated successfully.", "success")
            else:
                flash("Client not found.", "error")

        return redirect(url_for("superadmin.clients"))

    return render_template(
        "superadmin/clients.html",
        clients=load_clients(),
        plans=PLANS
    )


@superadmin_bp.route("/superadmin/plans")
@login_required
@superadmin_required
def plans():
    return render_template("superadmin/plans.html")


@superadmin_bp.route("/superadmin/updates", methods=["GET", "POST"])
@login_required
@superadmin_required
def updates():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        message = request.form.get("message", "").strip()
        status = request.form.get("status", "Published")
        image_url = ""

        image = request.files.get("image")

        if image and image.filename:
            ext = image.filename.rsplit(".", 1)[-1].lower()

            if ext in ALLOWED_EXT:
                filename = secure_filename(f"{uuid.uuid4().hex}_{image.filename}")
                upload_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
                image.save(upload_path)
                image_url = f"/static/uploads/updates/{filename}"
            else:
                flash("Invalid image format. Please upload png, jpg, jpeg, gif or webp.", "error")
                return redirect(url_for("superadmin.updates"))

        if title and message:
            items = load_updates()
            items.insert(0, {
                "id": uuid.uuid4().hex,
                "title": title,
                "message": message,
                "status": status,
                "image_url": image_url,
                "created_at": datetime.now().strftime("%d-%m-%Y %I:%M %p")
            })

            save_updates(items)
            flash("Update published successfully.", "success")
        else:
            flash("Title and message are required.", "error")

        return redirect(url_for("superadmin.updates"))

    return render_template("superadmin/updates.html", updates=load_updates())


@superadmin_bp.route("/updates")
@login_required
def client_updates():
    items = [u for u in load_updates() if u.get("status") == "Published"]
    return render_template("client/updates.html", updates=items)


@superadmin_bp.route("/client-data")
@login_required
@superadmin_required
def client_data():
    return render_template("superadmin/client_data.html")


@superadmin_bp.route("/subscription")
@login_required
def subscription():
    return render_template("superadmin/subscription.html")


@superadmin_bp.route("/audit")
@login_required
@superadmin_required
def audit():
    return render_template("superadmin/audit.html")
