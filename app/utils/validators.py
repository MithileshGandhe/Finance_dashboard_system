"""
Input validation schemas using marshmallow.
Each schema performs field-level validation and returns structured errors.
"""
import re
from datetime import date
from marshmallow import Schema, fields, validate, validates, ValidationError, pre_load


#  Reusable validators
PASSWORD_REGEX = re.compile(r"^.{6,128}$")  # min 6, max 128 chars


def validate_password(value: str) -> None:
    if not PASSWORD_REGEX.match(value):
        raise ValidationError("Password must be between 6 and 128 characters.")


#  Auth schemas
class RegisterSchema(Schema):
    username = fields.Str(
        required=True,
        validate=validate.Length(min=3, max=80),
        error_messages={"required": "Username is required."},
    )
    email = fields.Email(
        required=True,
        error_messages={"required": "Email is required.", "invalid": "Not a valid email address."},
    )
    password = fields.Str(
        required=True,
        load_only=True,
        validate=validate_password,
        error_messages={"required": "Password is required."},
    )
    full_name = fields.Str(validate=validate.Length(max=150), load_default=None)
    role = fields.Str(
        validate=validate.OneOf(["viewer", "analyst", "admin"]),
        load_default="viewer",
    )

    @pre_load
    def strip_strings(self, data, **kwargs):
        for key in ("username", "email", "full_name"):
            if isinstance(data.get(key), str):
                data[key] = data[key].strip()
        return data


class LoginSchema(Schema):
    username = fields.Str(required=True, error_messages={"required": "Username is required."})
    password = fields.Str(
        required=True,
        load_only=True,
        error_messages={"required": "Password is required."},
    )


#  User management schemas
class UpdateUserSchema(Schema):
    email = fields.Email(load_default=None)
    full_name = fields.Str(validate=validate.Length(max=150), load_default=None)
    role = fields.Str(
        validate=validate.OneOf(["viewer", "analyst", "admin"]),
        load_default=None,
    )
    is_active = fields.Bool(load_default=None)

    @pre_load
    def strip_strings(self, data, **kwargs):
        for key in ("email", "full_name"):
            if isinstance(data.get(key), str):
                data[key] = data[key].strip()
        return data


class ChangePasswordSchema(Schema):
    old_password = fields.Str(required=True, load_only=True)
    new_password = fields.Str(
        required=True, load_only=True, validate=validate_password
    )


#  Financial record schemas
class CreateRecordSchema(Schema):
    amount = fields.Decimal(
        required=True,
        places=2,
        as_string=False,
        validate=validate.Range(min=0.01, error="Amount must be greater than 0."),
        error_messages={"required": "Amount is required."},
    )
    record_type = fields.Str(
        required=True,
        validate=validate.OneOf(["income", "expense"]),
        error_messages={"required": "record_type is required (income or expense)."},
    )
    category = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=100),
        error_messages={"required": "Category is required."},
    )
    record_date = fields.Date(
        required=True,
        error_messages={"required": "record_date is required (YYYY-MM-DD)."},
    )
    description = fields.Str(validate=validate.Length(max=1000), load_default=None)

    @validates("record_date")
    def validate_date_not_future(self, value):
        if value > date.today():
            raise ValidationError("record_date cannot be in the future.")

    @pre_load
    def strip_strings(self, data, **kwargs):
        for key in ("category", "description"):
            if isinstance(data.get(key), str):
                data[key] = data[key].strip()
        return data


class UpdateRecordSchema(Schema):
    amount = fields.Decimal(
        places=2,
        as_string=False,
        validate=validate.Range(min=0.01, error="Amount must be greater than 0."),
        load_default=None,
    )
    record_type = fields.Str(
        validate=validate.OneOf(["income", "expense"]),
        load_default=None,
    )
    category = fields.Str(validate=validate.Length(min=1, max=100), load_default=None)
    record_date = fields.Date(load_default=None)
    description = fields.Str(validate=validate.Length(max=1000), load_default=None)

    @validates("record_date")
    def validate_date_not_future(self, value):
        if value and value > date.today():
            raise ValidationError("record_date cannot be in the future.")

    @pre_load
    def strip_strings(self, data, **kwargs):
        for key in ("category", "description"):
            if isinstance(data.get(key), str):
                data[key] = data[key].strip()
        return data


#  Schema helpers
def format_validation_errors(errors: dict) -> dict:
    """Flatten marshmallow error dict into a clean response body."""
    return {"error": "Validation failed", "details": errors}
