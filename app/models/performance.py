"""
Module 4 — Integrated Performance Analytics
Table: performance_records (materialized cache)
"""

from datetime import datetime, timezone
from sqlalchemy import CheckConstraint
from app.extensions import db


class PerformanceRecord(db.Model):
    """
    Cache table for employee performance metrics.
    Refreshed periodically by a background job (Celery Beat / APScheduler).

    Metric sources:
      lead_conversion_rate  ← leads (status='Customer' / total assigned)
      total_deal_value      ← SUM(leads.actual_value) where status='Customer'
      interaction_frequency ← COUNT(interactions) / days_in_period
      attendance_score      ← (days_present / working_days) × 100
      overall_score         ← weighted composite of above
    """
    __tablename__ = 'performance_records'
    __table_args__ = (
        db.UniqueConstraint('employee_id', 'period_start', 'period_end',
                            name='uq_emp_period'),
        CheckConstraint('period_end >= period_start',
                        name='ck_period_dates'),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'),
                            nullable=False)
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)

    # CRM metrics
    total_leads_assigned = db.Column(db.Integer, default=0)
    leads_converted = db.Column(db.Integer, default=0)
    lead_conversion_rate = db.Column(
        db.Numeric(5, 2), nullable=True,
        comment='(leads_converted / total_leads_assigned) * 100')
    total_deal_value = db.Column(
        db.Numeric(15, 2), default=0.00,
        comment='SUM of actual_value for converted leads')

    # Interaction metrics
    total_interactions = db.Column(db.Integer, default=0,
                                   comment='Interaction intensity counter')
    interaction_frequency = db.Column(
        db.Numeric(5, 2), nullable=True,
        comment='total_interactions / days_in_period')

    # HRMS metrics
    attendance_score = db.Column(
        db.Numeric(5, 2), nullable=True,
        comment='(days_present / working_days) * 100')

    # Composite
    overall_score = db.Column(db.Numeric(5, 2), nullable=True,
                              comment='Weighted composite score')
    computed_at = db.Column(db.DateTime(timezone=True),
                            default=lambda: datetime.now(timezone.utc),
                            comment='When this cache row was last refreshed')
    created_at = db.Column(db.DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc))

    # Relationships
    employee = db.relationship('Employee',
                               back_populates='performance_records')

    def __repr__(self):
        return (f'<PerformanceRecord emp={self.employee_id} '
                f'{self.period_start}–{self.period_end}>')
