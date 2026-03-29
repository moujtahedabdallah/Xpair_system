from .database import db
from .person import Person
from .availability_record import AvailabilityRecord
from .booking import Booking


class Employee(Person):
    # Inherits from person
    __tablename__ = 'employee'

    # Variables
    employeeID = db.Column(db.Integer, db.ForeignKey('person.id'), primary_key=True)
    experience_level = db.Column(db.String(50), nullable=False)
    position = db.Column(db.String(50), nullable=False)
    salary = db.Column(db.Float, nullable=False)
    working_hours = db.Column(db.Float, nullable=False)

    # Polymetric identity which essentially identifies this class as a part of the Person class
    __mapper_args__ = {
        'polymorphic_identity': 'employee',
    }

    # Methods
    def submit_availability(self, periodID, day, start_time, end_time):
        # Submits a new availability record for the given work week
        record = AvailabilityRecord(
            periodID=periodID,
            employeeID=self.employeeID,
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

        return True
        

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

        return True

    def add_job_notes(self, bookingID, job_notes):
        # Adds notes to an assigned booking
        booking = Booking.query.get(bookingID)
        
        if not booking:
            raise ValueError(f"Booking with ID {bookingID} not found.")
        if booking.assigned_employee != self.employeeID:
            raise PermissionError("You are not assigned to this booking.")
        
        booking.validate_notes(job_notes) # Trigger validation check
        booking.job_notes = job_notes
        db.session.commit()

    def view_job_details(self, bookingID):
        # Fetch the data from the database
        booking = Booking.query.get(bookingID)
            
        # Verify the job actually exists
        if not booking:
            raise ValueError(f"Booking with ID {bookingID} not found.")
                
        # Verify this specific employee is allowed to look at it
        if booking.assigned_employee != self.employeeID:
            raise PermissionError("You are not assigned to view this booking.")
                
        # Hand the data back to the user
        return booking
    
    def block_job(self, bookingID, block_reason) -> bool:
        # Fetch the data
        booking = Booking.query.get(bookingID)

        # Verify the job actually exists
        if not booking:
            raise ValueError(f"Booking with ID {bookingID} not found.")
                
        # Verify this specific employee is allowed to look at it
        if booking.assigned_employee != self.employeeID:
            raise PermissionError("You are not assigned to view this booking.")
        
        booking.update_block_status(True, block_reason)

        # Triggers email notification
        from .notification_service import NotificationService
        NotificationService().notify(
            recipient=None,
            event='manager_alert',
            occupant={'booking': booking, 'message': block_reason}
        )
        return True