from flask import Blueprint, render_template
from .auth import login_required
masters_bp = Blueprint("masters", __name__)
@masters_bp.route("/masters")
@login_required
def masters(): return render_template("masters/masters.html")
@masters_bp.route("/rate-contract")
@login_required
def rate_contract(): return render_template("masters/rate_contract.html")
