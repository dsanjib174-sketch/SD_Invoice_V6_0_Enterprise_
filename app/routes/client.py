from flask import Blueprint, render_template
from .auth import login_required
client_bp = Blueprint("client", __name__)
@client_bp.route("/company-profile")
@login_required
def company_profile(): return render_template("client/company_profile.html")
@client_bp.route("/branches")
@login_required
def branches(): return render_template("client/branches.html")
@client_bp.route("/users")
@login_required
def users(): return render_template("client/users.html")
@client_bp.route("/change-password")
@login_required
def change_password(): return render_template("client/change_password.html")
@client_bp.route("/communication")
@login_required
def communication(): return render_template("client/communication.html")
