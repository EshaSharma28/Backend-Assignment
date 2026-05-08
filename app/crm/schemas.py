from marshmallow import Schema, fields, validate

class LeadSchema(Schema):
    id = fields.Integer(dump_only=True)
    company_name = fields.String(required=True, validate=validate.Length(min=1, max=200))
    contact_name = fields.String(validate=validate.Length(max=200))
    contact_email = fields.Email()
    contact_phone = fields.String(validate=validate.Length(max=20))
    source = fields.String(validate=validate.Length(max=100))
    status = fields.String(validate=validate.OneOf(['Lead', 'Opportunity', 'Customer', 'Lost']))
    assigned_agent_id = fields.Integer(allow_none=True)
    estimated_value = fields.Decimal(as_string=True)
    actual_value = fields.Decimal(allow_none=True, as_string=True)
    converted_at = fields.DateTime(dump_only=True, allow_none=True)
    lost_reason = fields.String()
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

class LeadStatusHistorySchema(Schema):
    id = fields.Integer(dump_only=True)
    lead_id = fields.Integer(required=True)
    old_status = fields.String(allow_none=True)
    new_status = fields.String(required=True)
    changed_by = fields.Integer(required=True)
    changed_at = fields.DateTime(dump_only=True)
    notes = fields.String()

class InteractionSchema(Schema):
    id = fields.Integer(dump_only=True)
    lead_id = fields.Integer(dump_only=True)
    employee_id = fields.Integer(dump_only=True)
    type = fields.String(required=True, validate=validate.OneOf(['Call', 'Email', 'Meeting']))
    subject = fields.String(validate=validate.Length(max=255))
    notes = fields.String()
    interaction_date = fields.DateTime(required=True)
    duration_minutes = fields.Integer()
    created_at = fields.DateTime(dump_only=True)
