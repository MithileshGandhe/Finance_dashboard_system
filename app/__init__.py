from flask import Flask, jsonify
from app.config import config_map
from app.extensions import db, migrate, jwt, swagger


def create_app(config_name="development"):
    app = Flask(__name__)
    app.config.from_object(config_map[config_name])

    # ── Extensions ──────────────────────────────────────────────────────────
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    swagger.init_app(app)

    # ── Blueprints ───────────────────────────────────────────────────────────
    from app.blueprints.auth import auth_bp
    from app.blueprints.users import users_bp
    from app.blueprints.records import records_bp
    from app.blueprints.dashboard import dashboard_bp

    app.register_blueprint(auth_bp,      url_prefix="/api/auth")
    app.register_blueprint(users_bp,     url_prefix="/api/users")
    app.register_blueprint(records_bp,   url_prefix="/api/records")
    app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")

    # ── Global error handlers ────────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"error": "Method not allowed"}), 405

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Internal server error"}), 500

    return app
