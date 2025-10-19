from __future__ import annotations

from pathlib import Path

from flask import Flask, jsonify
from flask_cors import CORS

from .config import Config, get_config
from .extensions import db, login_manager, mail, migrate, scheduler
from .tasks.scheduler import register_jobs


def create_app(config_name: str | None = None) -> Flask:
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app_config: type[Config] = get_config(config_name)
    app.config.from_object(app_config)

    Path(app.config['STORAGE_DIR']).mkdir(parents=True, exist_ok=True)

    CORS(app)

    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    login_manager.init_app(app)
    if not scheduler.app:
        scheduler.init_app(app)
    register_jobs(scheduler)
    if not scheduler.running:
        scheduler.start()

    from .auth.routes import bp as auth_bp
    from .envelopes.routes import bp as envelopes_bp
    from .signing.routes import bp as signing_bp
    from .admin.routes import bp as admin_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(envelopes_bp, url_prefix='/api/envelopes')
    app.register_blueprint(signing_bp, url_prefix='/api/signing')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')

    @app.route('/healthz')
    def healthz():
        return jsonify({'status': 'ok'})

    return app
