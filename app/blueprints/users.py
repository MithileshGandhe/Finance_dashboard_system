from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.user import User, RoleEnum
from app.utils.validators import UpdateUserSchema, format_validation_errors
from app.middleware import admin_required, jwt_required_custom, _get_current_user

users_bp = Blueprint("users", __name__)


#  GET /api/users/                 (Admin only)
@users_bp.route("/", methods=["GET"])
@admin_required
def get_all_users():
    """
    Get all users (Admin only)
    ---
    tags:
      - User Management
    security:
      - BearerAuth: []
    responses:
      200:
        description: List of all active users
    """
    users = User.query.filter_by(is_deleted=False).all()
    return jsonify([u.to_dict() for u in users]), 200


#  GET /api/users/profile          (Any authenticated user)
@users_bp.route("/profile", methods=["GET"])
@jwt_required_custom
def get_profile():
    """
    Get the logged-in user's profile
    ---
    tags:
      - User Management
    security:
      - BearerAuth: []
    responses:
      200:
        description: Current user profile
    """
    user = _get_current_user()
    return jsonify(user.to_dict()), 200


#  PUT /api/users/<id>             (Admin only)
@users_bp.route("/<int:id>", methods=["PUT"])
@admin_required
def update_user(id):
    """
    Update a user's details (Admin only)
    ---
    tags:
      - User Management
    security:
      - BearerAuth: []
    parameters:
      - in: path
        name: id
        required: true
        type: integer
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            email:
              type: string
            full_name:
              type: string
            role:
              type: string
              enum: [viewer, analyst, admin]
            is_active:
              type: boolean
    responses:
      200:
        description: User updated successfully
      400:
        description: Validation error
      404:
        description: User not found
    """
    user = User.query.filter_by(id=id, is_deleted=False).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json(silent=True) or {}
    errors = UpdateUserSchema().validate(data)
    if errors:
        return jsonify(format_validation_errors(errors)), 400

    if data.get("email"):
        existing = User.query.filter_by(email=data["email"]).first()
        if existing and existing.id != id:
            return jsonify({"error": "Email already in use"}), 400
        user.email = data["email"]
    if data.get("full_name") is not None:
        user.full_name = data["full_name"]
    if data.get("role"):
        user.role = RoleEnum(data["role"])
    if data.get("is_active") is not None:
        user.is_active = data["is_active"]

    db.session.commit()
    return jsonify({"message": "User updated successfully", "user": user.to_dict()}), 200


#  PATCH /api/users/<id>/status    (Admin only)
@users_bp.route("/<int:id>/status", methods=["PATCH"])
@admin_required
def toggle_status(id):
    """
    Activate or deactivate a user (Admin only)
    ---
    tags:
      - User Management
    security:
      - BearerAuth: []
    parameters:
      - in: path
        name: id
        required: true
        type: integer
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [is_active]
          properties:
            is_active:
              type: boolean
    responses:
      200:
        description: Status updated
      404:
        description: User not found
    """
    user = User.query.filter_by(id=id, is_deleted=False).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json(silent=True) or {}
    if "is_active" not in data:
        return jsonify({"error": "is_active field is required"}), 400

    user.is_active = bool(data["is_active"])
    db.session.commit()
    status = "activated" if user.is_active else "deactivated"
    return jsonify({"message": f"User {status} successfully", "user": user.to_dict()}), 200


#  DELETE /api/users/<id>          (Admin only, soft delete)
@users_bp.route("/<int:id>", methods=["DELETE"])
@admin_required
def delete_user(id):
    """
    Soft-delete a user (Admin only)
    ---
    tags:
      - User Management
    security:
      - BearerAuth: []
    parameters:
      - in: path
        name: id
        required: true
        type: integer
    responses:
      200:
        description: User deleted successfully
      400:
        description: Cannot delete yourself
      404:
        description: User not found
    """
    user = User.query.filter_by(id=id, is_deleted=False).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    current = _get_current_user()
    if user.id == current.id:
        return jsonify({"error": "You cannot delete your own account"}), 400

    user.soft_delete()
    db.session.commit()
    return jsonify({"message": "User deleted successfully"}), 200
