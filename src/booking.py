from .database import db
import os

class Booking(db.Model):
    __tablename__ = 'booking'

    # Variables
    bookingID = db.Column(db.Integer, primary_key=True) # Primary key
    periodID = db.Column(db.Integer, nullable=True)  # work week identifier
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    is_blocked = db.Column(db.Boolean, default=False)
    block_reason = db.Column(db.String(200))
    booking_summary = db.Column(db.String(500))
    booking_status = db.Column(db.String(20), default='pending')  # pending, confirmed, cancelled, completed
    service_address = db.Column(db.String(300), nullable=True)   # where the detailing job takes place
    before_images = db.Column(db.String(500))  # file path e.g. '/uploads/bookings/123/before.jpg'
    after_images = db.Column(db.String(500))  # file path e.g. '/uploads/bookings/123/after.jpg'
    job_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())
    
    # Foreign Keys
    customerID = db.Column(db.Integer, db.ForeignKey('customer.customerID'), nullable=True)   # Nullable to support manager-blocked slots
    serviceID = db.Column(db.Integer, db.ForeignKey('service.serviceID'), nullable=True)       # Nullable to support manager-blocked slots
    vehicleID = db.Column(db.Integer, db.ForeignKey('vehicle.vehicleID'), nullable=True)       # Nullable to support manager-blocked slots
    assigned_employee = db.Column(db.Integer, db.ForeignKey('employee.employeeID'), nullable=True)
    
    # Relationships for SQLAlchemy
    customer = db.relationship('Customer', backref='bookings')
    service = db.relationship('Service', backref='bookings')
    vehicle = db.relationship('Vehicle', backref='bookings')
    employee = db.relationship('Employee', backref='assigned_jobs')
    
    # Methods
    def validate_job_status(self, new_status):
        # Validates if the new status matches one of the allowed status options
        valid_statuses = ['pending', 'confirmed', 'in_progress', 'completed', 'cancelled', 'on_hold']
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {valid_statuses}")
        return True

    def validate_images(self, file_name):
        # Validates image upload formats
        allowed_extensions = {'.png', '.jpg', '.jpeg'}
        ext = os.path.splitext(file_name)[1].lower()
        if ext not in allowed_extensions:
            raise ValueError("Invalid image format. Only PNG, JPG, or JPEG allowed.")
        return True
    
    def validate_notes(self, notes):
        # Validates string length for database limits
        if len(notes) > 1000:
            raise ValueError("Notes exceed maximum character limit of 1000.")
        return True

    def confirm(self) -> bool:
        # Confirms the booking
        self.booking_status = 'confirmed'
        db.session.commit()

        # Triggers email notification
        from .notification_service import NotificationService
        NotificationService().notify(recipient=self.customer, event='booking_confirmed', occupant=self)
        return True

    def reschedule(self, new_start_time, new_end_time):
        # Reschedules the booking to a new time
        self.start_time = new_start_time
        self.end_time = new_end_time
        self.date = new_start_time.date()  # Keep date field in sync with the new start time
        db.session.commit()

        return True

    def cancel(self) -> bool:
        # Cancels the booking
        self.booking_status = 'cancelled'
        db.session.commit()

        # Triggers email notification
        from .notification_service import NotificationService
        NotificationService().notify(recipient=self.customer, event='booking_cancelled', occupant=self)
        return True

    def update_job_status(self, new_status):
        # Updates the current status of the job
        self.validate_job_status(new_status) # Trigger validation check
        self.booking_status = new_status
        db.session.commit()

        return True

    def update_block_status(self, is_blocked, block_reason):
        # Blocks or unblocks a time slot with a reason
        self.is_blocked = is_blocked
        self.block_reason = block_reason

        if is_blocked:
            self.booking_status = 'on_hold'
        else:
            # If they unblock it, put it back to pending default.
            self.booking_status = 'pending'

        db.session.commit()

        return True

    def upload_before_images(self, file_path):
        # Saves the file path of before job images e.g. '/uploads/bookings/123/before.jpg'
        self.validate_images(file_path) # Triggers validation
        self.before_images = file_path
        db.session.commit()

        return True

    def upload_after_images(self, file_path):
        # Saves the file path of after job images e.g. '/uploads/bookings/123/after.jpg'
        self.validate_images(file_path) # Triggers validation
        self.after_images = file_path
        db.session.commit()

        return True

    def generate_booking_summary(self, selected_add_ons=None):
        # Auto-generates a booking summary
        service_name = self.service.service_name
        cust_name = self.customer.first_name
        car = f"{self.vehicle.year} {self.vehicle.model}"

        summary = service_name
        
        # If add-ons exist, join them into a single string
        if selected_add_ons:
            summary = f"{service_name} with {', '.join(selected_add_ons)}"
        
        self.booking_summary = f"{summary} for {cust_name}'s {car}."
        db.session.commit()
        return self.booking_summary