from flask import Blueprint

auth = Blueprint("auth", __name__, url_prefix="/auth")

# Import routes agar otomatis terdaftar
from . import routes  # noqa: F401