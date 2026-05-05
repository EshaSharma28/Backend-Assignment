"""
Module 3 — CRM Models
Tables: leads, lead_status_history, interactions
Note removed from interaction_type ENUM — notes are a field, not a type.
"""

from datetime import datetime, timezone
from sqlalchemy import Enum as PgEnum
from app.extensions import db

LeadStatus = PgEnum(
    'Lead', 'Opportunity', 'Customer', 'Lost',
    name='lead_status', create_type=True,
)

InteractionType = PgEnum(
    'Call', 'Email', 'Meeting',
    name='interaction_type', create_type=True,
)


class Lead(db.Model):
    """
    Sales pipeline entity: Lead → Opportunity → Customer | Lost.
    assigned_agent_id links to employees(id) — the sales agent bridge.
    """
    __tablename__ = 'leads'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    company_name = db.Column(db.String(200), nullable=False)
    contact_name = db.Column(db.String(200), nullable=True)
    contact_email = db.Column(db.String(255), nullable=True)
    contact_phone = db.Column(db.String(20), nullable=True)
    source = db.Column(db.String(100), nullable=True)
    status = db.Column(LeadStatus, default='Lead', nullable=False,
                       comment='Pipeline stage')
    assigned_agent_id = db.Column(
        db.Integer, db.ForeignKey('employees.id'), nullable=True,
        comment='FK to Employee acting as sales agent')
    estimated_value = db.Column(db.Numeric(15, 2), default=0.00,
                                comment='Projected deal size')
    actual_value = db.Column(db.Numeric(15, 2), nullable=True,
                             comment='Recorded on conversion to Customer')
    converted_at = db.Column(db.DateTime(timezone=True), nullable=True,
                             comment='When status → Customer')
    lost_reason = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    assigned_agent = db.relationship('Employee',
                                     back_populates='assigned_leads',
                                     foreign_keys=[assigned_agent_id])
    status_history = db.relationship('LeadStatusHistory',
                                     back_populates='lead',
                                     cascade='all, delete-orphan',
                                     order_by='LeadStatusHistory.changed_at')
    interactions = db.relationship('Interaction', back_populates='lead',
                                   cascade='all, delete-orphan',
                                   order_by='Interaction.interaction_date.desc()')

    def __repr__(self):
        return f'<Lead {self.company_name} [{self.status}]>'


class LeadStatusHistory(db.Model):
    """Audit trail for every pipeline transition."""
    __tablename__ = 'lead_status_history'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'), nullable=False)
    old_status = db.Column(LeadStatus, nullable=True)
    new_status = db.Column(LeadStatus, nullable=False)
    changed_by = db.Column(db.Integer, db.ForeignKey('employees.id'),
                           nullable=False)
    changed_at = db.Column(db.DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc))
    notes = db.Column(db.Text, nullable=True)

    lead = db.relationship('Lead', back_populates='status_history')
    changed_by_employee = db.relationship('Employee',
                                          foreign_keys=[changed_by])

    def __repr__(self):
        return f'<StatusHistory lead={self.lead_id} {self.old_status}→{self.new_status}>'


class Interaction(db.Model):
    """
    Logs calls, emails, and meetings against a lead.
    Notes field captures details — 'Note' is NOT an interaction type.
    """
    __tablename__ = 'interactions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'),
                            nullable=False)
    type = db.Column(InteractionType, nullable=False,
                     comment='Call | Email | Meeting')
    subject = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True,
                      comment='Detailed notes about the interaction')
    interaction_date = db.Column(
        db.DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc))
    duration_minutes = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc))

    lead = db.relationship('Lead', back_populates='interactions')
    employee = db.relationship('Employee', back_populates='interactions')

    def __repr__(self):
        return f'<Interaction {self.type} lead={self.lead_id}>'
