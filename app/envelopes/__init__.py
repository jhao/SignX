from flask import Blueprint

bp = Blueprint('envelopes', __name__)

from . import routes  # noqa: E402,F401
