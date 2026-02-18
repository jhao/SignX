from __future__ import annotations

from flask import Flask, render_template
from flask_cors import CORS

from .config import Config, get_config
from .extensions import db, login_manager, migrate


def create_app(config_name: str | None = None) -> Flask:
    app = Flask(__name__)
    app_config: type[Config] = get_config(config_name)
    app.config.from_object(app_config)

    CORS(app)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    from .auth.routes import bp as auth_bp
    from .companies.routes import bp as companies_bp
    from .employees.routes import bp as employees_bp
    from .projects.routes import bp as projects_bp
    from .finance.routes import bp as finance_bp
    from .tools.routes import bp as tools_bp
    from .admin.routes import bp as admin_bp

    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(companies_bp, url_prefix='/api/v1/companies')
    app.register_blueprint(employees_bp, url_prefix='/api/v1/employees')
    app.register_blueprint(projects_bp, url_prefix='/api/v1/projects')
    app.register_blueprint(finance_bp, url_prefix='/api/v1/finance')
    app.register_blueprint(tools_bp, url_prefix='/api/v1/tools')
    app.register_blueprint(admin_bp, url_prefix='/api/v1/admin')

    @app.get('/healthz')
    def healthz():
        return {'status': 'ok'}

    @app.get('/')
    def index():
        return render_template('index.html')

    return app
