from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session
from .auth import login_required
import os, json, uuid
from datetime import datetime

documents_bp = Blueprint("documents", __name__)

QUOTATION_FILE = "quotations.json"
ROC_FILE = "rate_contracts.json"


def _json_path(filename):
    return os.path.join(current_app.config["UPLOAD_FOLDER"], filename)


def load_json(filename):
    path = _json_path(filename)

    if not os.path.exists(path):
        return []

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(filename, data):
    os.makedirs(os.path.dirname(_json_path(filename)), exist_ok=True)

    with open(_json_path(filename), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def current_user_email():
    return session.get("user") or session.get("email") or ""


def is_superadmin():
    return session.get("login_type") == "superadmin" or session.get("role") == "superadmin"


@documents_bp.route("/quotation", methods=["GET", "POST"])
@login_required
def quotation():
    quotations = load_json(QUOTATION_FILE)
    contracts = load_json(ROC_FILE)
    user_email = current_user_email()

    if request.method == "POST":
        action = request.form.get("action")

        if action == "save_quotation":
            quotation_no = request.form.get("quotation_no", "").strip()
            vendor_name = request.form.get("vendor_name", "").strip()
            customer_name = request.form.get("customer_name", "").strip()
            product_name = request.form.get("product_name", "").strip()
            hsn_code = request.form.get("hsn_code", "").strip()
            unit = request.form.get("unit", "").strip()
            rate = request.form.get("rate", "").strip()
            gst_percent = request.form.get("gst_percent", "").strip()
            remarks = request.form.get("remarks", "").strip()

            if not quotation_no:
                quotation_no = f"QT-{datetime.now().strftime('%Y%m%d%H%M%S')}"

            if not vendor_name or not product_name or not rate:
                flash("Vendor Name, Product/Service Name and Rate are required.", "error")
                return redirect(url_for("documents.quotation"))

            quotations.insert(0, {
                "id": uuid.uuid4().hex,
                "quotation_no": quotation_no,
                "vendor_name": vendor_name,
                "customer_name": customer_name,
                "product_name": product_name,
                "hsn_code": hsn_code,
                "unit": unit,
                "rate": rate,
                "gst_percent": gst_percent,
                "remarks": remarks,
                "status": "Pending",
                "client_email": user_email,
                "created_by": user_email,
                "created_at": datetime.now().strftime("%d-%m-%Y %I:%M %p")
            })

            save_json(QUOTATION_FILE, quotations)
            flash("Quotation saved successfully.", "success")

        elif action == "update_quotation":
            quotation_id = request.form.get("quotation_id")

            for q in quotations:
                if q.get("id") == quotation_id:

                    if not is_superadmin() and q.get("client_email") != user_email:
                        flash("You cannot edit another client's quotation.", "error")
                        return redirect(url_for("documents.quotation"))

                    if q.get("status") == "Approved":
                        flash("Approved quotation cannot be edited.", "error")
                        return redirect(url_for("documents.quotation"))

                    q["quotation_no"] = request.form.get("quotation_no", "").strip()
                    q["vendor_name"] = request.form.get("vendor_name", "").strip()
                    q["customer_name"] = request.form.get("customer_name", "").strip()
                    q["product_name"] = request.form.get("product_name", "").strip()
                    q["hsn_code"] = request.form.get("hsn_code", "").strip()
                    q["unit"] = request.form.get("unit", "").strip()
                    q["rate"] = request.form.get("rate", "").strip()
                    q["gst_percent"] = request.form.get("gst_percent", "").strip()
                    q["remarks"] = request.form.get("remarks", "").strip()
                    q["updated_at"] = datetime.now().strftime("%d-%m-%Y %I:%M %p")
                    break

            save_json(QUOTATION_FILE, quotations)
            flash("Quotation updated successfully.", "success")

        elif action == "approve_quotation":
            quotation_id = request.form.get("quotation_id")

            for q in quotations:
                if q.get("id") == quotation_id:

                    if not is_superadmin() and q.get("client_email") != user_email:
                        flash("You cannot approve another client's quotation.", "error")
                        return redirect(url_for("documents.quotation"))

                    if q.get("status") == "Approved":
                        flash("Quotation already approved.", "error")
                        return redirect(url_for("documents.quotation"))

                    q["status"] = "Approved"
                    q["approved_by"] = user_email
                    q["approved_at"] = datetime.now().strftime("%d-%m-%Y %I:%M %p")

                    contracts.insert(0, {
                        "id": uuid.uuid4().hex,
                        "vendor_name": q.get("vendor_name", ""),
                        "product_name": q.get("product_name", ""),
                        "hsn_code": q.get("hsn_code", ""),
                        "unit": q.get("unit", ""),
                        "rate": q.get("rate", ""),
                        "gst_percent": q.get("gst_percent", ""),
                        "valid_from": datetime.now().strftime("%Y-%m-%d"),
                        "valid_to": "",
                        "remarks": "Auto created from approved quotation " + q.get("quotation_no", ""),
                        "source": "Approved Quotation",
                        "status": "Active",
                        "client_email": q.get("client_email", user_email),
                        "created_by": user_email,
                        "created_at": datetime.now().strftime("%d-%m-%Y %I:%M %p")
                    })
                    break

            save_json(QUOTATION_FILE, quotations)
            save_json(ROC_FILE, contracts)
            flash("Quotation approved and rate added to ROC successfully.", "success")

        return redirect(url_for("documents.quotation"))

    if not is_superadmin():
        quotations = [q for q in quotations if q.get("client_email") == user_email]

    return render_template("documents/quotation.html", quotations=quotations)


@documents_bp.route("/proforma")
@login_required
def proforma():
    return render_template("documents/proforma.html")


@documents_bp.route("/invoice")
@login_required
def invoice():
    return render_template("documents/invoice.html")


@documents_bp.route("/delivery-challan")
@login_required
def delivery_challan():
    return render_template("documents/delivery_challan.html")
