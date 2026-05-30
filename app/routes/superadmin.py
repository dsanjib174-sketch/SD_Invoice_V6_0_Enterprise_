from flask import Blueprint, render_template, request, redirect, url_for, current_app, flash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os, json, uuid
from .auth import login_required, superadmin_required

superadmin_bp = Blueprint("superadmin", __name__)

DATA_FILE = "updates.json"
CLIENTS_FILE = "clients.json"

ALLOWED_EXT = {"png", "jpg", "jpeg", "gif", "webp"}

PLANS_FILE = "plans.json"


def _plans_path():
    return os.path.join(current_app.config["UPLOAD_FOLDER"], PLANS_FILE)


def default_plans():
    return [
        {
            "id": uuid.uuid4().hex,
            "plan": "Basic",
            "price": "4999",
            "user_limit": "2",
            "branch_limit": "1",
            "invoice_limit": "100",
            "validity_years": "1",
            "status": "Active"
        },
        {
            "id": uuid.uuid4().hex,
            "plan": "Standard",
            "price": "9999",
            "user_limit": "5",
            "branch_limit": "3",
            "invoice_limit": "500",
            "validity_years": "1",
            "status": "Active"
        },
        {
            "id": uuid.uuid4().hex,
            "plan": "Premium",
            "price": "19999",
            "user_limit": "10",
            "branch_limit": "10",
            "invoice_limit": "2000",
            "validity_years": "1",
            "status": "Active"
        },
        {
            "id": uuid.uuid4().hex,
            "plan": "Enterprise",
            "price": "49999",
            "user_limit": "Unlimited",
            "branch_limit": "Unlimited",
            "invoice_limit": "Unlimited",
            "validity_years": "1",
            "status": "Active"
        }
    ]


def load_plans():
    path = _plans_path()
    if not os.path.exists(path):
        plans = default_plans()
        save_plans(plans)
        return plans

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_plans(items):
    with open(_plans_path(), "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)


@superadmin_bp.route("/superadmin/plans", methods=["GET", "POST"])
@login_required
@superadmin_required
def plans():
    plans_data = load_plans()

    if request.method == "POST":
        action = request.form.get("action")

        if action == "add":
            plans_data.insert(0, {
                "id": uuid.uuid4().hex,
                "plan": request.form.get("plan", "").strip(),
                "price": request.form.get("price", "").strip(),
                "user_limit": request.form.get("user_limit", "").strip(),
                "branch_limit": request.form.get("branch_limit", "").strip(),
                "invoice_limit": request.form.get("invoice_limit", "").strip(),
                "validity_years": "1",
                "status": "Active"
            })
            save_plans(plans_data)
            flash("Plan added successfully.", "success")

        elif action == "update":
            plan_id = request.form.get("plan_id")

            for p in plans_data:
                if p.get("id") == plan_id:
                    p["plan"] = request.form.get("plan", "").strip()
                    p["price"] = request.form.get("price", "").strip()
                    p["user_limit"] = request.form.get("user_limit", "").strip()
                    p["branch_limit"] = request.form.get("branch_limit", "").strip()
                    p["invoice_limit"] = request.form.get("invoice_limit", "").strip()
                    p["validity_years"] = "1"
                    p["status"] = request.form.get("status", "Active")
                    break

            save_plans(plans_data)
            flash("Plan updated successfully.", "success")

        return redirect(url_for("superadmin.plans"))

    return render_template("superadmin/plans.html", plans=plans_data)

@superadmin_bp.route("/subscription")
@login_required
def subscription():
    return render_template("superadmin/subscription.html")


@superadmin_bp.route("/audit")
@login_required
@superadmin_required
def audit():
    return render_template("superadmin/audit.html")
