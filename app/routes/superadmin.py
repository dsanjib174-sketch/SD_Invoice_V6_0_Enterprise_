from flask import Blueprint, render_template, request, redirect, url_for, current_app, flash
from werkzeug.utils import secure_filename
from datetime import datetime
import os, json, uuid
from .auth import login_required, superadmin_required

superadmin_bp = Blueprint("superadmin", __name__)

DATA_FILE = "updates.json"
ALLOWED_EXT = {"png", "jpg", "jpeg", "gif", "webp"}


def _data_path():
    return os.path.join(current_app.config["UPLOAD_FOLDER"], DATA_FILE)


def load_updates():
    path = _data_path()
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_updates(items):
    with open(_data_path(), "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)


@superadmin_bp.route("/superadmin/clients")
@login_required
@superadmin_required
def clients(): return render_template("superadmin/clients.html")

@superadmin_bp.route("/superadmin/plans")
@login_required
@superadmin_required
def plans(): return render_template("superadmin/plans.html")

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
                image.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
                image_url = f"/static/uploads/updates/{filename}"
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
def client_data(): return render_template("superadmin/client_data.html")

@superadmin_bp.route("/subscription")
@login_required
def subscription(): return render_template("superadmin/subscription.html")

@superadmin_bp.route("/audit")
@login_required
@superadmin_required
def audit(): return render_template("superadmin/audit.html")
