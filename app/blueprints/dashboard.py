from flask import Blueprint, jsonify, request
from app.extensions import db
from app.models.financial_record import FinancialRecord, RecordTypeEnum
from app.middleware import analyst_required, viewer_required
from sqlalchemy import func
from datetime import date

dashboard_bp = Blueprint("dashboard", __name__)


#  GET /api/dashboard/summary      (Analyst + Admin)
@dashboard_bp.route("/summary", methods=["GET"])
@analyst_required
def get_summary():
    """
    Dashboard summary: totals, balance, categories & recent activity (Analyst/Admin)
    ---
    tags:
      - Dashboard
    security:
      - BearerAuth: []
    responses:
      200:
        description: Aggregated summary data
    """
    income_total = (
        db.session.query(func.sum(FinancialRecord.amount))
        .filter_by(record_type=RecordTypeEnum.income, is_deleted=False)
        .scalar() or 0
    )
    expense_total = (
        db.session.query(func.sum(FinancialRecord.amount))
        .filter_by(record_type=RecordTypeEnum.expense, is_deleted=False)
        .scalar() or 0
    )
    net_balance = income_total - expense_total

    # Category-wise totals (income + expense combined)
    category_rows = (
        db.session.query(
            FinancialRecord.category,
            FinancialRecord.record_type,
            func.sum(FinancialRecord.amount).label("total"),
        )
        .filter_by(is_deleted=False)
        .group_by(FinancialRecord.category, FinancialRecord.record_type)
        .all()
    )
    category_totals = {}
    for cat, rtype, total in category_rows:
        if cat not in category_totals:
            category_totals[cat] = {"income": 0, "expense": 0}
        category_totals[cat][rtype.value] = float(total)

    # 5 most recent records
    recent = (
        FinancialRecord.query.filter_by(is_deleted=False)
        .order_by(FinancialRecord.created_at.desc())
        .limit(5)
        .all()
    )

    return jsonify(
        {
            "total_income": float(income_total),
            "total_expenses": float(expense_total),
            "net_balance": float(net_balance),
            "category_wise_totals": category_totals,
            "recent_activity": [r.to_dict() for r in recent],
        }
    ), 200


#  GET /api/dashboard/trends/monthly   (Analyst + Admin)
@dashboard_bp.route("/trends/monthly", methods=["GET"])
@analyst_required
def monthly_trends():
    """
    Monthly income vs expense trends for the current year (Analyst/Admin)
    ---
    tags:
      - Dashboard
    security:
      - BearerAuth: []
    responses:
      200:
        description: Month-by-month income and expense totals
    """
    year = request.args.get("year", date.today().year, type=int)

    rows = (
        db.session.query(
            func.month(FinancialRecord.record_date).label("month"),
            FinancialRecord.record_type,
            func.sum(FinancialRecord.amount).label("total"),
        )
        .filter(
            func.year(FinancialRecord.record_date) == year,
            FinancialRecord.is_deleted == False,
        )
        .group_by(func.month(FinancialRecord.record_date), FinancialRecord.record_type)
        .all()
    )

    months = {}
    for month, rtype, total in rows:
        if month not in months:
            months[month] = {"month": month, "income": 0, "expense": 0}
        months[month][rtype.value] = float(total)

    # Sort by month number
    trend_list = sorted(months.values(), key=lambda x: x["month"])
    return jsonify({"year": year, "trends": trend_list}), 200


#  GET /api/dashboard/recent        (All roles)
@dashboard_bp.route("/recent", methods=["GET"])
@viewer_required
def recent_activity():
    """
    Get the most recent financial records (All roles)
    ---
    tags:
      - Dashboard
    security:
      - BearerAuth: []
    parameters:
      - in: query
        name: limit
        type: integer
        default: 10
    responses:
      200:
        description: Recent records list
    """
    limit = request.args.get("limit", 10, type=int)
    limit = min(limit, 100)  # cap at 100

    records = (
        FinancialRecord.query.filter_by(is_deleted=False)
        .order_by(FinancialRecord.created_at.desc())
        .limit(limit)
        .all()
    )
    return jsonify({"records": [r.to_dict() for r in records]}), 200
