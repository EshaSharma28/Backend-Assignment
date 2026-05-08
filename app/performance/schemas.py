from marshmallow import Schema, fields, validate

class PerformanceRecordSchema(Schema):
    id = fields.Integer(dump_only=True)
    employee_id = fields.Integer(required=True)
    period_start = fields.Date(required=True)
    period_end = fields.Date(required=True)
    
    # CRM metrics
    total_leads_assigned = fields.Integer(dump_only=True)
    leads_converted = fields.Integer(dump_only=True)
    lead_conversion_rate = fields.Decimal(dump_only=True, as_string=True)
    total_deal_value = fields.Decimal(dump_only=True, as_string=True)
    
    # Interaction metrics
    total_interactions = fields.Integer(dump_only=True)
    interaction_frequency = fields.Decimal(dump_only=True, as_string=True)
    
    # HRMS metrics
    attendance_score = fields.Decimal(dump_only=True, as_string=True)
    
    # Composite
    overall_score = fields.Decimal(dump_only=True, as_string=True)
    computed_at = fields.DateTime(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
