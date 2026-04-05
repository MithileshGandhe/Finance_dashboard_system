from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
)
from app.extensions import db
from app.models.user import User
from app.utils.validators import RegisterSchema, LoginSchema, format_validation_errors

auth_bp = Blueprint("auth", __name__)


#  POST /api/auth/register
@auth_bp.route("/register", methods=["POST"])
def register():
    """
    Register a new user
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [username, email, password]
          properties:
            username:
              type: string
              example: johndoe
            email:
              type: string
              example: john@example.com
            password:
              type: string
              example: secret123
            full_name:
              type: string
              example: John Doe
            role:
              type: string
              enum: [viewer, analyst, admin]
              example: viewer
    responses:
      201:
        description: User registered successfully
      400:
        description: Validation error or duplicate username/email
    """
    data = request.get_json(silent=True) or {}
    errors = RegisterSchema().validate(data)
    if errors:
        return jsonify(format_validation_errors(errors)), 400

    if User.query.filter_by(username=data["username"]).first():
        return jsonify({"error": "Username already exists"}), 400
    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Email already registered"}), 400

    user = User(
        username=data["username"],
        email=data["email"],
        full_name=data.get("full_name"),
        role=data.get("role", "viewer"),
    )
    user.set_password(data["password"])
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "User registered successfully", "user": user.to_dict()}), 201


#  POST /api/auth/login
@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Login and get JWT tokens
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [username, password]
          properties:
            username:
              type: string
              example: admin
            password:
              type: string
              example: admin123
    responses:
      200:
        description: Login successful – returns access_token and refresh_token
      401:
        description: Invalid credentials
    """
    data = request.get_json(silent=True) or {}
    errors = LoginSchema().validate(data)
    if errors:
        return jsonify(format_validation_errors(errors)), 400

    user = User.query.filter_by(
        username=data["username"], is_active=True, is_deleted=False
    ).first()

    if not user or not user.check_password(data["password"]):
        return jsonify({"error": "Invalid username or password"}), 401

    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    return jsonify(
        {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": user.to_dict(),
        }
    ), 200


#  POST /api/auth/refresh
@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    """
    Refresh access token using refresh token
    ---
    tags:
      - Authentication
    security:
      - BearerAuth: []
    responses:
      200:
        description: New access token issued
      401:
        description: Invalid or expired refresh token
    """
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    return jsonify({"access_token": access_token}), 200
