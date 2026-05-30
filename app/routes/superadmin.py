from flask import Blueprint, render_template, request, redirect, url_for, current_app, flash, session
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os, json, uuid
from .auth import login_required, superadmin_required

superadmin_bp = Blueprint("superadmin", __name__)

DATA_FILE = "updates.json"
CLIENTS_FILE = "clients.json"
PLANS_FILE = "plans.json"
SUBSCRIPTIONS_FILE = "subscriptions.json"

ALLOWED_EXT = {"png", "jpg", "jpeg", "gif", "webp"}


def _json_path(filename):
    return os.path.join(current_app.config["UPLOAD_FOLDER"], filename)


def load_json(path, default_value):
    if not os.path.exists(path):
        return default_value
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, items):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)


def load_updates():
    return load_json(_json_path(DATA_FILE), [])


def save_updates(items):
    save_json(_json_path(DATA_FILE), items)


def load_clients():
    return load_json(_json_path(CLIENTS_FILE), [])


def save_clients(items):
    save_json(_json_path(CLIENTS_FILE), items)


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
    path = _json_path(PLANS_FILE)
    if not os.path.exists(path):
        plans = default_plans()
        save_plans(plans)
        return plans
    return load_json(path, [])


def save_plans(items):
    save_json(_json_path(PLANS_FILE), items)


def load_subscriptions():
    return load_json(_json_path(SUBSCRIPTIONS_FILE), [])


def save_subscriptions(items):
    save_json(_json_path(SUBSCRIPTIONS_FILE), items)


def get_current_user_email():
    return (
        session.get("email")
        or session.get("user_email")
        or session.get("username")
        or ""
    )


def is_superadmin_user():
    return (
        session.get("role") == "superadmin"
        or get_current_user_email() == "superadmin@sdinvoice.com"
    )


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
        plans=load_plans()
    )


@superadmin_bp.route("/superadmin/plans", methods=["GET", "POST"])
@login_required
@superadmin_required
def plans():
    plans_data = load_plans()

    if request.method == "POST":
        action = request.form.get("action")

        if action == "add":
            plan_name = request.form.get("plan", "").strip()
            price = request.form.get("price", "").strip()
            user_limit = request.form.get("user_limit", "").strip()
            branch_limit = request.form.get("branch_limit", "").strip()
            invoice_limit = request.form.get("invoice_limit", "").strip()

            if plan_name and price:
                plans_data.insert(0, {
                    "id": uuid.uuid4().hex,
                    "plan": plan_name,
                    "price": price,
                    "user_limit": user_limit,
                    "branch_limit": branch_limit,
                    "invoice_limit": invoice_limit,
                    "validity_years": "1",
                    "status": "Active"
                })
                save_plans(plans_data)
                flash("Plan added successfully.", "success")
            else:
                flash("Plan name and price are required.", "error")

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


@superadmin_bp.route("/subscription", methods=["GET", "POST"])
@login_required
def subscription:
    subscriptions = load_subscriptions()
    clients_data = load_clients()
    user_email = get_current_user_email()

    if request.method == "POST":
        if not is_superadmin_user():
            flash("Only Super Admin can generate subscription invoices.", "error")
            return redirect(url_for("superadmin.subscription"))

        action = request.form.get("action")

        if action == "create_invoice":
            client_id = request.form.get("client_id")
            amount = request.form.get("amount", "0").strip()
            selected_client = None

            for c in clients_data:
                if c.get("id") == client_id:
                    selected_client = c
                    break

            if selected_client:
                invoice_no = f"SUB-{datetime.now().strftime('%Y%m%d%H%M%S')}"

                subscriptions.insert(0, {
                    "id": uuid.uuid4().hex,
                    "invoice_no": invoice_no,
                    "client_id": selected_client.get("id"),
                    "client_company": selected_client.get("company"),
                    "client_email": selected_client.get("email"),
                    "plan_name": selected_client.get("plan_name"),
                    "active_date": selected_client.get("active_date"),
                    "expire_date": selected_client.get("expire_date"),
                    "amount": amount,
                    "status": "Generated",
                    "created_at": datetime.now().strftime("%d-%m-%Y %I:%M %p")
                })

                save_subscriptions(subscriptions)
                flash("Subscription invoice generated successfully.", "success")
            else:
                flash("Client not found.", "error")

        return redirect(url_for("superadmin.subscription"))

    if is_superadmin_user():
        visible_subscriptions = subscriptions
    else:
        visible_subscriptions = [
            s for s in subscriptions
            if s.get("client_email") == user_email
        ]

    return render_template(
        "superadmin/subscription.html",
        subscriptions=visible_subscriptions,
        clients=clients_data,
        user_email=user_email,
        is_superadmin=is_superadmin_user()
    )


@superadmin_bp.route("/audit")
@login_required
@superadmin_required
def audit():
    return render_template("superadmin/audit.html")
