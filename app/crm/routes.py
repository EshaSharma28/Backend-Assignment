from datetime import datetime, timezone
from flask import request, jsonify, g
from app.crm import crm_bp
from app.extensions import db
from app.models.crm import Lead, Interaction, LeadStatusHistory
from app.models.hrms import Employee
from app.crm.schemas import LeadSchema, InteractionSchema, LeadStatusHistorySchema
from app.auth.decorators import require_auth, require_permission
from app.utils.background import run_async, send_assignment_notification

lead_schema = LeadSchema()
leads_schema = LeadSchema(many=True)
interaction_schema = InteractionSchema()
interactions_schema = InteractionSchema(many=True)
history_schema = LeadStatusHistorySchema(many=True)

@crm_bp.route('/leads', methods=['GET'])
@require_auth
@require_permission('leads', 'can_read')
def get_leads():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    # Scoping: Sales agents only see leads assigned to them
    query = Lead.query
    if g.current_user.role_id == 3: # Sales
        if not g.current_user.employee:
            return jsonify({
                'leads': [],
                'total': 0,
                'pages': 0,
                'current_page': page
            }), 200
        query = query.filter_by(assigned_agent_id=g.current_user.employee.id)
    
    # Apply pagination
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'leads': leads_schema.dump(pagination.items),
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': pagination.page
    }), 200

@crm_bp.route('/leads/<int:id>', methods=['GET'])
@require_auth
@require_permission('leads', 'can_read')
def get_lead(id):
    lead = db.session.get(Lead, id)
    if not lead:
        return jsonify({'message': 'Lead not found'}), 404
    
    # Scoping check for Sales
    if g.current_user.role_id == 3:
        if not g.current_user.employee or lead.assigned_agent_id != g.current_user.employee.id:
            return jsonify({'message': 'Access denied: Lead not assigned to you'}), 403
            
    return jsonify(lead_schema.dump(lead)), 200

@crm_bp.route('/leads', methods=['POST'])
@require_auth
@require_permission('leads', 'can_write')
def create_lead():
    data = request.get_json()
    errors = lead_schema.validate(data)
    if errors:
        return jsonify(errors), 400
    
    assigned_agent_id = data.get('assigned_agent_id')
    if assigned_agent_id:
        agent = db.session.get(Employee, assigned_agent_id)
        if not agent or not agent.is_sales_agent:
            return jsonify({'message': 'Invalid assignment: Employee is not a Sales Agent'}), 400

    new_lead = Lead(
        company_name=data['company_name'],
        contact_name=data.get('contact_name'),
        contact_email=data.get('contact_email'),
        contact_phone=data.get('contact_phone'),
        source=data.get('source'),
        status=data.get('status', 'Lead'),
        assigned_agent_id=assigned_agent_id,
        estimated_value=data.get('estimated_value', 0.00)
    )
    
    db.session.add(new_lead)
    db.session.commit()

    # Async Notification if agent is assigned
    if new_lead.assigned_agent_id:
        agent = db.session.get(Employee, new_lead.assigned_agent_id)
        if agent and agent.user:
            run_async(send_assignment_notification, agent.user.email, new_lead.company_name)
    
    return jsonify(lead_schema.dump(new_lead)), 201

@crm_bp.route('/leads/<int:id>', methods=['PATCH'])
@require_auth
@require_permission('leads', 'can_write')
def update_lead(id):
    lead = db.session.get(Lead, id)
    if not lead:
        return jsonify({'message': 'Lead not found'}), 404
    
    data = request.get_json()
    # Partial validation: only validate fields present in the request
    errors = lead_schema.validate(data, partial=True)
    if errors:
        return jsonify(errors), 400
    
    was_unassigned = lead.assigned_agent_id is None
    
    # Validate assignment if agent is being updated
    new_agent_id = data.get('assigned_agent_id')
    if new_agent_id and new_agent_id != lead.assigned_agent_id:
        agent = db.session.get(Employee, new_agent_id)
        if not agent or not agent.is_sales_agent:
            return jsonify({'message': 'Invalid assignment: Employee is not a Sales Agent'}), 400

    # Update only the fields provided in the body
    for key, value in data.items():
        if hasattr(lead, key):
            setattr(lead, key, value)
    
    db.session.commit()

    # Async Notification if newly assigned
    if was_unassigned and lead.assigned_agent_id:
        agent = db.session.get(Employee, lead.assigned_agent_id)
        if agent and agent.user:
            run_async(send_assignment_notification, agent.user.email, lead.company_name)
    
    return jsonify(lead_schema.dump(lead)), 200

@crm_bp.route('/leads/<int:id>/interactions', methods=['GET'])
@require_auth
@require_permission('leads', 'can_read')
def get_lead_interactions(id):
    lead = db.session.get(Lead, id)
    if not lead:
        return jsonify({'message': 'Lead not found'}), 404
    
    interactions = Interaction.query.filter_by(lead_id=id).all()
    return jsonify(interactions_schema.dump(interactions)), 200

@crm_bp.route('/leads/<int:id>/interactions', methods=['POST'])
@require_auth
@require_permission('leads', 'can_write')
def log_interaction(id):
    lead = db.session.get(Lead, id)
    if not lead:
        return jsonify({'message': 'Lead not found'}), 404
    
    data = request.get_json()
    errors = interaction_schema.validate(data)
    if errors:
        return jsonify(errors), 400
    
    # Use current user as the employee logging the interaction if not specified
    employee_id = data.get('employee_id')
    if not employee_id:
        # Check if current user has an associated employee profile
        if not g.current_user.employee:
            return jsonify({'message': 'User has no employee profile'}), 400
        employee_id = g.current_user.employee.id

    new_interaction = Interaction(
        lead_id=id,
        employee_id=employee_id,
        type=data['type'],
        subject=data.get('subject'),
        notes=data.get('notes'),
        interaction_date=data.get('interaction_date', datetime.now(timezone.utc)),
        duration_minutes=data.get('duration_minutes')
    )
    
    db.session.add(new_interaction)
    db.session.commit()
    
    return jsonify(interaction_schema.dump(new_interaction)), 201

@crm_bp.route('/leads/<int:id>/history', methods=['GET'])
@require_auth
@require_permission('leads', 'can_read')
def get_lead_history(id):
    lead = db.session.get(Lead, id)
    if not lead:
        return jsonify({'message': 'Lead not found'}), 404
    
    history = LeadStatusHistory.query.filter_by(lead_id=id).order_by(LeadStatusHistory.changed_at.desc()).all()
    return jsonify(history_schema.dump(history)), 200

@crm_bp.route('/leads/<int:id>/status', methods=['PATCH'])
@require_auth
@require_permission('leads', 'can_write')
def update_lead_status(id):
    lead = db.session.get(Lead, id)
    if not lead:
        return jsonify({'message': 'Lead not found'}), 404
    
    data = request.get_json()
    new_status = data.get('status')
    if not new_status:
        return jsonify({'message': 'Status is required'}), 400
    
    old_status = lead.status
    lead.status = new_status
    
    # Log history
    employee_id = g.current_user.employee.id if g.current_user.employee else None
    history = LeadStatusHistory(
        lead_id=id,
        old_status=old_status,
        new_status=new_status,
        changed_by=employee_id,
        notes=data.get('notes')
    )
    
    if new_status == 'Customer':
        lead.converted_at = datetime.now(timezone.utc)
        lead.actual_value = data.get('actual_value', lead.estimated_value)
    elif new_status == 'Lost':
        lead.lost_reason = data.get('lost_reason')

    db.session.add(history)
    db.session.commit()
    
    return jsonify(lead_schema.dump(lead)), 200
