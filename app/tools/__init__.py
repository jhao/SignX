from flask import Blueprint

bp = Blueprint('tools', __name__)

from . import routes  # noqa: E402,F401
