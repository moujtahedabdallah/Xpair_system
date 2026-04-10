from .database import db
from datetime import date

class SchedulingPeriod(db.Model):
    __tablename__ = 'scheduling_period'

    # Variables
    periodID   = db.Column(db.Integer, primary_key=True)
    label      = db.Column(db.String(100), nullable=False)    # e.g. "April 14-27, 2026"
    start_date = db.Column(db.Date, nullable=False)
    end_date   = db.Column(db.Date, nullable=False)
    due_date   = db.Column(db.Date, nullable=False)           # deadline for employees to submit
    status     = db.Column(db.String(20), default='upcoming') # upcoming, open, closed

    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    # Foreign Key — manager who created the period
    created_by = db.Column(db.Integer, db.ForeignKey('manager.managerID'), nullable=True)

    # Relationships
    manager        = db.relationship('Manager', backref='scheduling_periods')
    availabilities = db.relationship('AvailabilityRecord', backref='period',
                                     foreign_keys='AvailabilityRecord.periodID',
                                     primaryjoin='SchedulingPeriod.periodID == AvailabilityRecord.periodID')


    # METHODS 

    def is_open(self):
        # Returns True if the period is currently open for employee submissions
        # A period is open when its status is 'open' and today is on or before the due date
        return self.status == 'open' and date.today() <= self.due_date

    def get_employee_submission(self, employee_id):
        # Returns all AvailabilityRecord rows submitted by a given employee for this period
        # Used to display existing submissions on the enter/review screens
        from .availability_record import AvailabilityRecord
        return AvailabilityRecord.query.filter_by(
            periodID=self.periodID,
            employeeID=employee_id
        ).order_by(AvailabilityRecord.start_time.asc()).all()

    def get_submission_status(self, employee_id):
        # Returns a string indicating whether an employee has submitted for this period
        # Returns 'submitted' if records exist, 'not_submitted' otherwise
        from .availability_record import AvailabilityRecord
        exists = AvailabilityRecord.query.filter_by(
            periodID=self.periodID,
            employeeID=employee_id
        ).first()
        return 'submitted' if exists else 'not_submitted'

    def close(self):
        # Closes the scheduling period — called by manager once the submission window ends
        # Prevents further employee edits by setting status to 'closed'
        self.status = 'closed'
        db.session.commit()
        return True