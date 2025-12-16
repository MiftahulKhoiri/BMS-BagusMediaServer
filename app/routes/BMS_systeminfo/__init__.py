from flask import Blueprint

systeminfo = Blueprint(
    "systeminfo",
    __name__,
    url_prefix="/system"
)

from . import routes