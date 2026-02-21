from .database import db
from datetime import datetime

class AvailabilityRecord(db.Model):
    __tablename__ = 'availability_record'

    # Variables
    availabilityID = db.Column(db.Integer, primary_key=True)
    periodID = db.Column(db.Integer, nullable=False)  # work week identifier
    status = db.Column(db.String(20), default='pending')  # pending, approved, changes_requested
    manager_notes = db.Column(db.Text)
    reviewed_at = db.Column(db.DateTime)
    day = db.Column(db.String(20), nullable=False)  # e.g. Monday, Tuesday
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    # Foreign Keys
    employeeID = db.Column(db.Integer, db.ForeignKey('employee.employeeID'), nullable=False)
    managerID = db.Column(db.Integer, db.ForeignKey('manager.managerID'), nullable=True)
    
    # Relationships for SQLAlchemy
    employee = db.relationship('Employee', backref='availabilities')
    manager = db.relationship('Manager', backref='reviewed_availabilities')
    # Methods
    def validate_availability(self):
        # Checks that start time is before end time
        return self.start_time < self.end_time

    def update_availability_status(self, new_status):
        # Updates the status of the availability record
        self.status = new_status
        db.session.commit()

    def mark_approved(self):
        # Marks the availability record as approved and records the review time
        self.status = 'approved'
        self.reviewed_at = datetime.now()
        db.session.commit()

    def mark_changes_requested(self, manager_notes):
        # Marks the availability record as needing changes with manager notes and records the review time
        self.status = 'changes_requested'
        self.manager_notes = manager_notes
        self.reviewed_at = datetime.now()
        db.session.commit()