from .database import db
from .person import Person
from .availability_record import AvailabilityRecord
from .booking import Booking


class Employee(Person):
    __tablename__ = 'employee'

    # Variables
    employeeID = db.Column(db.Integer, db.ForeignKey('person.id'), primary_key=True)
    experience_level = db.Column(db.String(50), nullable=False)
    position = db.Column(db.String(50), nullable=False)
    salary = db.Column(db.Float, nullable=False)
    working_hours = db.Column(db.Float, nullable=False)
  

    # Methods
    def submit_availability(self, periodID, day, start_time, end_time):
        # Submits a new availability record for the given work week
        record = AvailabilityRecord(
            periodID=periodID,
            employee_id=self.employeeID,
            day=day,
            start_time=start_time,
            end_time=end_time,
            status='pending',
        )
        if not record.validate_availability():
            raise ValueError("Start time must be before end time.")
        db.session.add(record)
        db.session.commit()
        return record

    def view_assigned_schedule(self, periodID):
        # Returns all confirmed bookings assigned to this employee for a given work week
        return Booking.query.filter_by(
            periodID=periodID,
            assigned_employee=self.employeeID
        ).order_by(Booking.start_time).all()

    def view_job_history(self):
        # Returns all completed jobs assigned to this employee
        return Booking.query.filter_by(
            assigned_employee=self.employeeID,
            booking_status='completed'
        ).order_by(Booking.date).all()

    def update_job_status(self, bookingID, booking_status):
        # Updates the status of an assigned booking
        booking = Booking.query.get(bookingID)
        if not booking:
            raise ValueError(f"Booking with ID {bookingID} not found.")
        if booking.assigned_employee != self.employeeID:
            raise PermissionError("You are not assigned to this booking.")
        booking.update_job_status(booking_status)

    def upload_job_images(self, bookingID, before_images=None, after_images=None):
        # Uploads before and/or after images for a booking
        booking = Booking.query.get(bookingID)
        if not booking:
            raise ValueError(f"Booking with ID {bookingID} not found.")
        if booking.assigned_employee != self.employeeID:
            raise PermissionError("You are not assigned to this booking.")
        if before_images:
            booking.upload_before_images(before_images)
        if after_images:
            booking.upload_after_images(after_images)

    def add_job_notes(self, bookingID, job_notes):
        # Adds notes to an assigned booking
        booking = Booking.query.get(bookingID)
        if not booking:
            raise ValueError(f"Booking with ID {bookingID} not found.")
        if booking.assigned_employee != self.employeeID:
            raise PermissionError("You are not assigned to this booking.")
        booking.job_notes = job_notes
        db.session.commit()
