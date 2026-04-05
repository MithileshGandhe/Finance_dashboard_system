from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.financial_record import FinancialRecord, RecordTypeEnum
from app.utils.validators import CreateRecordSchema, UpdateRecordSchema, format_validation_errors
from app.middleware import admin_required, viewer_required, _get_current_user

records_bp = Blueprint("records", __name__)


#  POST /api/records/              (Admin only)
@records_bp.route("/", methods=["POST"])
@admin_required
def create_record():
    """
    Create a new financial record (Admin only)
    ---
    tags:
      - Financial Records
    security:
      - BearerAuth: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [amount, record_type, category, record_date]
          properties:
            amount:
              type: number
              example: 1500.00
            record_type:
              type: string
              enum: [income, expense]
            category:
              type: string
              example: Salary
            record_date:
              type: string
              format: date
              example: "2024-04-01"
            description:
              type: string
              example: Monthly paycheck
    responses:
      201:
        description: Record created
      400:
        description: Validation error
    """
    data = request.get_json(silent=True) or {}
    errors = CreateRecordSchema().validate(data)
    if errors:
        return jsonify(format_validation_errors(errors)), 400

    user = _get_current_user()
    record = FinancialRecord(
        amount=data["amount"],
        record_type=data["record_type"],
        category=data["category"],
        record_date=data["record_date"],
        description=data.get("description"),
        created_by_id=user.id,
    )
    db.session.add(record)
    db.session.commit()
    return jsonify({"message": "Record created successfully", "record": record.to_dict()}), 201


#  GET /api/records/               (All roles – with filters + search)
@records_bp.route("/", methods=["GET"])
@viewer_required
def get_records():
    """
    Get all financial records with optional filters and search
    ---
    tags:
      - Financial Records
    security:
      - BearerAuth: []
    parameters:
      - in: query
        name: record_type
        type: string
        enum: [income, expense]
      - in: query
        name: category
        type: string
      - in: query
        name: start_date
        type: string
        format: date
      - in: query
        name: end_date
        type: string
        format: date
      - in: query
        name: search
        type: string
        description: Search in category or description
    responses:
      200:
        description: List of records
    """
    query = FinancialRecord.query.filter_by(is_deleted=False)

    category    = request.args.get("category")
    record_type = request.args.get("record_type")
    start_date  = request.args.get("start_date")
    end_date    = request.args.get("end_date")
    search      = request.args.get("search")

    if record_type:
        query = query.filter(FinancialRecord.record_type == record_type)
    if category:
        query = query.filter(FinancialRecord.category.ilike(f"%{category}%"))
    if start_date:
        query = query.filter(FinancialRecord.record_date >= start_date)
    if end_date:
        query = query.filter(FinancialRecord.record_date <= end_date)
    if search:
        like = f"%{search}%"
        query = query.filter(
            db.or_(
                FinancialRecord.category.ilike(like),
                FinancialRecord.description.ilike(like),
            )
        )

    records = query.order_by(FinancialRecord.record_date.desc()).all()
    return jsonify({"total": len(records), "records": [r.to_dict() for r in records]}), 200


#  GET /api/records/<id>           (All roles)
@records_bp.route("/<int:id>", methods=["GET"])
@viewer_required
def get_record(id):
    """
    Get a single financial record by ID
    ---
    tags:
      - Financial Records
    security:
      - BearerAuth: []
    parameters:
      - in: path
        name: id
        required: true
        type: integer
    responses:
      200:
        description: Record details
      404:
        description: Record not found
    """
    record = FinancialRecord.query.filter_by(id=id, is_deleted=False).first()
    if not record:
        return jsonify({"error": "Record not found"}), 404
    return jsonify(record.to_dict()), 200


#  PUT /api/records/<id>           (Admin only)
@records_bp.route("/<int:id>", methods=["PUT"])
@admin_required
def update_record(id):
    """
    Update a financial record (Admin only)
    ---
    tags:
      - Financial Records
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
            amount:
              type: number
            record_type:
              type: string
              enum: [income, expense]
            category:
              type: string
            record_date:
              type: string
              format: date
            description:
              type: string
    responses:
      200:
        description: Record updated
      404:
        description: Record not found
    """
    record = FinancialRecord.query.filter_by(id=id, is_deleted=False).first()
    if not record:
        return jsonify({"error": "Record not found"}), 404

    data = request.get_json(silent=True) or {}
    errors = UpdateRecordSchema().validate(data)
    if errors:
        return jsonify(format_validation_errors(errors)), 400

    if data.get("amount")      is not None: record.amount      = data["amount"]
    if data.get("record_type") is not None: record.record_type = data["record_type"]
    if data.get("category")    is not None: record.category    = data["category"]
    if data.get("record_date") is not None: record.record_date = data["record_date"]
    if "description"           in data:     record.description = data["description"]

    db.session.commit()
    return jsonify({"message": "Record updated successfully", "record": record.to_dict()}), 200


#  DELETE /api/records/<id>        (Admin only – soft delete)
@records_bp.route("/<int:id>", methods=["DELETE"])
@admin_required
def delete_record(id):
    """
    Soft-delete a financial record (Admin only)
    ---
    tags:
      - Financial Records
    security:
      - BearerAuth: []
    parameters:
      - in: path
        name: id
        required: true
        type: integer
    responses:
      200:
        description: Record deleted
      404:
        description: Record not found
    """
    record = FinancialRecord.query.filter_by(id=id, is_deleted=False).first()
    if not record:
        return jsonify({"error": "Record not found"}), 404

    record.soft_delete()
    db.session.commit()
    return jsonify({"message": "Record soft-deleted successfully"}), 200
