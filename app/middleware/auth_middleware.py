from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from app.models.user import User


def _get_current_user() -> User | None:
    """Fetch the current user from the JWT identity."""
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=user_id, is_deleted=False, is_active=True).first()
    return user


#  Base decorator factory
def _role_required(*allowed_roles):
    """
    Generic decorator that enforces JWT auth + role membership.
    Usage: @_role_required("admin") or @_role_required("admin", "analyst")
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # 1. Verify JWT is present and valid
            try:
                verify_jwt_in_request()
            except Exception as exc:
                return jsonify({"error": "Missing or invalid token", "detail": str(exc)}), 401

            # 2. Load user
            user = _get_current_user()
            if not user:
                return jsonify({"error": "User not found or account is disabled"}), 401

            # 3. Check role
            if user.role.value not in allowed_roles:
                return jsonify(
                    {
                        "error": "Access denied",
                        "detail": (
                            f"This action requires one of the following roles: "
                            f"{', '.join(allowed_roles)}. "
                            f"Your role: {user.role.value}"
                        ),
                    }
                ), 403

            return fn(*args, **kwargs)
        return wrapper
    return decorator


#  Public convenience decorators
def jwt_required_custom(fn):
    """Require a valid JWT; any active role is accepted."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
        except Exception as exc:
            return jsonify({"error": "Missing or invalid token", "detail": str(exc)}), 401

        user = _get_current_user()
        if not user:
            return jsonify({"error": "User not found or account is disabled"}), 401

        return fn(*args, **kwargs)
    return wrapper


def admin_required(fn):
    """Only admin can access."""
    return _role_required("admin")(fn)


def analyst_required(fn):
    """Admin and analyst can access."""
    return _role_required("admin", "analyst")(fn)


def viewer_required(fn):
    """All authenticated roles can access (viewer, analyst, admin)."""
    return _role_required("viewer", "analyst", "admin")(fn)
