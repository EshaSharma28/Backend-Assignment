from datetime import datetime, time, timezone
from flask import request, jsonify, g
from sqlalchemy import func
from app.performance import performance_bp
from app.extensions import db
from app.models.hrms import Employee, DailyAttendance
from app.models.crm import Lead, Interaction
from app.models.performance import PerformanceRecord
from app.performance.schemas import PerformanceRecordSchema
from app.auth.decorators import require_auth, require_permission

performance_schema = PerformanceRecordSchema()
performances_schema = PerformanceRecordSchema(many=True)

@performance_bp.route('/calculate/<int:employee_id>', methods=['POST'])
@require_auth
@require_permission('performance', 'can_write')
def calculate_performance(employee_id):
    data = request.get_json()
    errors = performance_schema.validate(data, partial=True)
    if errors:
        return jsonify(errors), 400
    
    # We need to extract the dates for our queries
    period_start = datetime.strptime(data['period_start'], '%Y-%m-%d').date()
    period_end = datetime.strptime(data['period_end'], '%Y-%m-%d').date()
    if period_end < period_start:
        return jsonify({'message': 'period_end cannot be before period_start'}), 400

    period_start_at = datetime.combine(period_start, time.min, tzinfo=timezone.utc)
    period_end_at = datetime.combine(period_end, time.max, tzinfo=timezone.utc)
    
    employee = db.session.get(Employee, employee_id)
    if not employee:
        return jsonify({'message': 'Employee not found'}), 404

    # 1. CRM Metrics
    total_leads = Lead.query.filter(
        Lead.assigned_agent_id == employee_id,
        Lead.created_at >= period_start_at,
        Lead.created_at <= period_end_at
    ).count()
    
    converted_leads = Lead.query.filter(
        Lead.assigned_agent_id == employee_id,
        Lead.status == 'Customer',
        Lead.converted_at >= period_start_at,
        Lead.converted_at <= period_end_at
    ).count()
    
    conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0
    
    total_deal_value = db.session.query(func.sum(Lead.actual_value)).filter(
        Lead.assigned_agent_id == employee_id,
        Lead.status == 'Customer',
        Lead.converted_at >= period_start_at,
        Lead.converted_at <= period_end_at
    ).scalar() or 0

    # 2. Interaction Metrics
    total_interactions = Interaction.query.filter(
        Interaction.employee_id == employee_id,
        Interaction.interaction_date >= period_start_at,
        Interaction.interaction_date <= period_end_at
    ).count()

    # 3. HRMS Metrics (Attendance)
    days_present = DailyAttendance.query.filter(
        DailyAttendance.employee_id == employee_id,
        DailyAttendance.date >= period_start,
        DailyAttendance.date <= period_end,
        DailyAttendance.status == 'Present'
    ).count()
    
    # Assume 22 working days per month if period is roughly a month, 
    # or just use total days in period for simplicity here.
    total_days = (period_end - period_start).days + 1
    attendance_score = (days_present / total_days * 100) if total_days > 0 else 0

    interaction_frequency = total_interactions / total_days if total_days > 0 else 0
    deal_value_score = min(float(total_deal_value) / 100000 * 100, 100)

    # 4. Composite Score (40% conversion, 30% value, 20% interactions, 10% attendance)
    overall_score = (
        (conversion_rate * 0.4) + 
        (deal_value_score * 0.3) +
        (min(attendance_score, 100) * 0.1) +
        (min(total_interactions * 5, 100) * 0.2) # Assuming 20 interactions is a "perfect" 100 score
    )

    # Update or Create Cache Record
    record = PerformanceRecord.query.filter_by(
        employee_id=employee_id,
        period_start=period_start,
        period_end=period_end
    ).first()
    
    if not record:
        record = PerformanceRecord(
            employee_id=employee_id,
            period_start=period_start,
            period_end=period_end
        )
        db.session.add(record)
    
    record.total_leads_assigned = total_leads
    record.leads_converted = converted_leads
    record.lead_conversion_rate = conversion_rate
    record.total_deal_value = total_deal_value
    record.total_interactions = total_interactions
    record.interaction_frequency = interaction_frequency
    record.attendance_score = attendance_score
    record.overall_score = overall_score
    record.computed_at = datetime.now(timezone.utc)
    
    db.session.commit()
    
    return jsonify(performance_schema.dump(record)), 200

@performance_bp.route('/employee/<int:employee_id>', methods=['GET'])
@require_auth
@require_permission('performance', 'can_read')
def get_employee_performance(employee_id):
    records = PerformanceRecord.query.filter_by(employee_id=employee_id).order_by(PerformanceRecord.period_start.desc()).all()
    return jsonify(performances_schema.dump(records)), 200
