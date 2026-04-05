import os
from app import create_app
from app.extensions import db
from app.models.user import User, RoleEnum

app = create_app(os.getenv("FLASK_ENV", "development"))


@app.cli.command("init-db")
def init_db_command():
    """Create all tables and seed a default admin user."""
    _init_db()


def _init_db():
    """Internal helper shared between CLI and direct run."""
    db.create_all()
    admin = User.query.filter_by(username="admin").first()
    if not admin:
        admin = User(
            username="admin",
            email="admin@example.com",
            full_name="System Administrator",
            role=RoleEnum.admin,
        )
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()
        print(" Admin user created  →  username: admin  |  password: admin123")
    else:
        print(" Admin user already exists.")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "init-db":
        with app.app_context():
            _init_db()
    else:
        app.run(host="0.0.0.0", port=5000, debug=True)
