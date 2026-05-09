from marshmallow import Schema, fields, validate

class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.String(required=True, validate=validate.Length(min=6))

class RegisterSchema(Schema):
    email = fields.Email(required=True)
    password = fields.String(required=True, validate=validate.Length(min=6))
    role_id = fields.Integer(load_only=True)
    
class UserSchema(Schema):
    id = fields.UUID(dump_only=True)
    email = fields.Email()
    role_id = fields.Integer()
    is_active = fields.Boolean()
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class UserRoleUpdateSchema(Schema):
    role_id = fields.Integer()
    role = fields.String(validate=validate.OneOf(['Admin', 'HR', 'Sales']))


class UserStatusUpdateSchema(Schema):
    is_active = fields.Boolean(required=True)
