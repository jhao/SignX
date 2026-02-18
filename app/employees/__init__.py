from flask import Blueprint

bp = Blueprint('employees', __name__)

from . import routes  # noqa: E402,F401
