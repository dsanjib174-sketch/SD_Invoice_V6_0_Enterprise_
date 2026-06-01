from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session
from .auth import login_required
import os, json, uuid
from datetime import datetime

documents_bp = Blueprint("documents", __name__)

QUOTATION_FILE = "quotations.json"
PROFORMA_FILE = "proformas.json"
INVOICE_FILE = "invoices.json"
DELIVERY_CHALLAN_FILE = "delivery_challans.json"
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


def get_financial_year():
    today = datetime.now()
    year = today.year

    if today.month >= 4:
        return f"{str(year)[-2:]}-{str(year + 1)[-2:]}"
    return f"{str(year - 1)[-2:]}-{str(year)[-2:]}"


def generate_doc_no(prefix, existing_docs):
    fy = get_financial_year()
    count = len(existing_docs) + 1
    return f"SD/{prefix}/{fy}/{str(count).zfill(3)}"


def load_roc():
    return load_json(ROC_FILE)


def get_vendor_names():
    contracts = load_roc()
    vendors = sorted(set([
        c.get("vendor_name", "")
        for c in contracts
        if c.get("vendor_name") and c.get("status") == "Active"
    ]))
    return vendors


def visible_data(data):
    if is_superadmin():
        return data

    user_email = current_user_email()
    return [d for d in data if d.get("client_email") == user_email]


@documents_bp.route("/quotation", methods=["GET", "POST"])
@login_required
def quotation():
    quotations = load_json(QUOTATION_FILE)
    contracts = load_roc()
    vendors = get_vendor_names()
    user_email = current_user_email()

    if request.method == "POST":
        action = request.form.get("action")

        if action == "save_quotation":
            quotation_no = request.form.get("quotation_no", "").strip()
            if not quotation_no:
                quotation_no = generate_doc_no("QT", quotations)

            quotations.insert(0, {
                "id": uuid.uuid4().hex,
                "quotation_no": quotation_no,
                "vendor_name": request.form.get("vendor_name", "").strip(),
                "customer_name": request.form.get("customer_name", "").strip(),
                "product_name": request.form.get("product_name", "").strip(),
                "hsn_code": request.form.get("hsn_code", "").strip(),
                "unit": request.form.get("unit", "").strip(),
                "qty": request.form.get("qty", "1").strip(),
                "rate": request.form.get("rate", "0").strip(),
                "gst_percent": request.form.get("gst_percent", "0").strip(),
                "taxable_amount": request.form.get("taxable_amount", "0").strip(),
                "cgst": request.form.get("cgst", "0").strip(),
                "sgst": request.form.get("sgst", "0").strip(),
                "igst": request.form.get("igst", "0").strip(),
                "total_gst": request.form.get("total_gst", "0").strip(),
                "grand_total": request.form.get("grand_total", "0").strip(),
                "remarks": request.form.get("remarks", "").strip(),
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
                    if q.get("status") == "Approved":
                        flash("Approved quotation cannot be edited.", "error")
                        return redirect(url_for("documents.quotation"))

                    q["quotation_no"] = request.form.get("quotation_no", "").strip()
                    q["vendor_name"] = request.form.get("vendor_name", "").strip()
                    q["customer_name"] = request.form.get("customer_name", "").strip()
                    q["product_name"] = request.form.get("product_name", "").strip()
                    q["hsn_code"] = request.form.get("hsn_code", "").strip()
                    q["unit"] = request.form.get("unit", "").strip()
                    q["qty"] = request.form.get("qty", "1").strip()
                    q["rate"] = request.form.get("rate", "0").strip()
                    q["gst_percent"] = request.form.get("gst_percent", "0").strip()
                    q["taxable_amount"] = request.form.get("taxable_amount", "0").strip()
                    q["cgst"] = request.form.get("cgst", "0").strip()
                    q["sgst"] = request.form.get("sgst", "0").strip()
                    q["igst"] = request.form.get("igst", "0").strip()
                    q["total_gst"] = request.form.get("total_gst", "0").strip()
                    q["grand_total"] = request.form.get("grand_total", "0").strip()
                    q["remarks"] = request.form.get("remarks", "").strip()
                    q["updated_at"] = datetime.now().strftime("%d-%m-%Y %I:%M %p")
                    break

            save_json(QUOTATION_FILE, quotations)
            flash("Quotation updated successfully.", "success")

        elif action == "approve_quotation":
            quotation_id = request.form.get("quotation_id")

            for q in quotations:
                if q.get("id") == quotation_id:
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

    return render_template(
        "documents/quotation.html",
        quotations=visible_data(quotations),
        vendors=vendors,
        contracts=contracts,
        doc_no=generate_doc_no("QT", quotations)
    )


@documents_bp.route("/proforma", methods=["GET", "POST"])
@login_required
def proforma():
    proformas = load_json(PROFORMA_FILE)
    contracts = load_roc()
    vendors = get_vendor_names()
    user_email = current_user_email()

    if request.method == "POST":
        proforma_no = request.form.get("proforma_no", "").strip()
        if not proforma_no:
            proforma_no = generate_doc_no("PI", proformas)

        proformas.insert(0, {
            "id": uuid.uuid4().hex,
            "proforma_no": proforma_no,
            "vendor_name": request.form.get("vendor_name", "").strip(),
            "customer_name": request.form.get("customer_name", "").strip(),
            "product_name": request.form.get("product_name", "").strip(),
            "hsn_code": request.form.get("hsn_code", "").strip(),
            "unit": request.form.get("unit", "").strip(),
            "qty": request.form.get("qty", "1").strip(),
            "rate": request.form.get("rate", "0").strip(),
            "gst_percent": request.form.get("gst_percent", "0").strip(),
            "taxable_amount": request.form.get("taxable_amount", "0").strip(),
            "cgst": request.form.get("cgst", "0").strip(),
            "sgst": request.form.get("sgst", "0").strip(),
            "igst": request.form.get("igst", "0").strip(),
            "total_gst": request.form.get("total_gst", "0").strip(),
            "grand_total": request.form.get("grand_total", "0").strip(),
            "status": "Pending",
            "client_email": user_email,
            "created_at": datetime.now().strftime("%d-%m-%Y %I:%M %p")
        })

        save_json(PROFORMA_FILE, proformas)
        flash("Proforma invoice saved successfully.", "success")
        return redirect(url_for("documents.proforma"))

    return render_template(
        "documents/proforma.html",
        proformas=visible_data(proformas),
        vendors=vendors,
        contracts=contracts,
        doc_no=generate_doc_no("PI", proformas)
    )


@documents_bp.route("/invoice", methods=["GET", "POST"])
@login_required
def invoice():
    invoices = load_json(INVOICE_FILE)
    contracts = load_roc()
    vendors = get_vendor_names()
    user_email = current_user_email()

    if request.method == "POST":
        invoice_no = request.form.get("invoice_no", "").strip()
        if not invoice_no:
            invoice_no = generate_doc_no("INV", invoices)

        invoices.insert(0, {
            "id": uuid.uuid4().hex,
            "invoice_no": invoice_no,
            "vendor_name": request.form.get("vendor_name", "").strip(),
            "customer_name": request.form.get("customer_name", "").strip(),
            "product_name": request.form.get("product_name", "").strip(),
            "hsn_code": request.form.get("hsn_code", "").strip(),
            "unit": request.form.get("unit", "").strip(),
            "qty": request.form.get("qty", "1").strip(),
            "rate": request.form.get("rate", "0").strip(),
            "gst_percent": request.form.get("gst_percent", "0").strip(),
            "taxable_amount": request.form.get("taxable_amount", "0").strip(),
            "cgst": request.form.get("cgst", "0").strip(),
            "sgst": request.form.get("sgst", "0").strip(),
            "igst": request.form.get("igst", "0").strip(),
            "total_gst": request.form.get("total_gst", "0").strip(),
            "grand_total": request.form.get("grand_total", "0").strip(),
            "status": "Generated",
            "client_email": user_email,
            "created_at": datetime.now().strftime("%d-%m-%Y %I:%M %p")
        })

        save_json(INVOICE_FILE, invoices)
        flash("Tax invoice saved successfully.", "success")
        return redirect(url_for("documents.invoice"))

    return render_template(
        "documents/invoice.html",
        invoices=visible_data(invoices),
        vendors=vendors,
        contracts=contracts,
        doc_no=generate_doc_no("INV", invoices)
    )


@documents_bp.route("/delivery-challan", methods=["GET", "POST"])
@login_required
def delivery_challan():
    challans = load_json(DELIVERY_CHALLAN_FILE)
    contracts = load_roc()
    vendors = get_vendor_names()
    user_email = current_user_email()

    if request.method == "POST":
        challan_no = request.form.get("challan_no", "").strip()
        if not challan_no:
            challan_no = generate_doc_no("DC", challans)

        challans.insert(0, {
            "id": uuid.uuid4().hex,
            "challan_no": challan_no,
            "vendor_name": request.form.get("vendor_name", "").strip(),
            "customer_name": request.form.get("customer_name", "").strip(),
            "product_name": request.form.get("product_name", "").strip(),
            "hsn_code": request.form.get("hsn_code", "").strip(),
            "unit": request.form.get("unit", "").strip(),
            "qty": request.form.get("qty", "1").strip(),
            "client_email": user_email,
            "created_at": datetime.now().strftime("%d-%m-%Y %I:%M %p")
        })

        save_json(DELIVERY_CHALLAN_FILE, challans)
        flash("Delivery challan saved successfully.", "success")
        return redirect(url_for("documents.delivery_challan"))

    return render_template(
        "documents/delivery_challan.html",
        challans=visible_data(challans),
        vendors=vendors,
        contracts=contracts,
        doc_no=generate_doc_no("DC", challans)
    )
