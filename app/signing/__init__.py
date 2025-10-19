from flask import Blueprint

bp = Blueprint('signing', __name__)

from . import routes  # noqa: E402,F401
