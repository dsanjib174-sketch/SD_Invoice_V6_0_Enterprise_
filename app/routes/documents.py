from flask import Blueprint, render_template
from .auth import login_required

documents_bp = Blueprint("documents", __name__)
@documents_bp.route("/quotation")
@login_required
def quotation(): return render_template("documents/quotation.html")
@documents_bp.route("/proforma")
@login_required
def proforma(): return render_template("documents/proforma.html")
@documents_bp.route("/invoice")
@login_required
def invoice(): return render_template("documents/invoice.html")
@documents_bp.route("/invoice/preview")
@login_required
def invoice_preview(): return render_template("invoice/professional_invoice.html")
@documents_bp.route("/delivery-challan")
@login_required
def delivery_challan(): return render_template("documents/delivery_challan.html")
@documents_bp.route("/receipts")
@login_required
def receipts(): return render_template("documents/receipts.html")
@documents_bp.route("/credit-note")
@login_required
def credit_note(): return render_template("documents/credit_note.html")
