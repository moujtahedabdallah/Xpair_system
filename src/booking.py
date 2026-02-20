from .database import db

class Booking(db.Model):
    __tablename__ = 'booking'

    # Variables
    bookingID = db.Column(db.Integer, primary_key=True)
    periodID = db.Column(db.Integer, nullable=True)  # work week identifier
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    is_blocked = db.Column(db.Boolean, default=False)
    block_reason = db.Column(db.String(200))
    booking_status = db.Column(db.String(20), default='pending')  # pending, confirmed, cancelled, completed
    assigned_employee = db.Column(db.Integer, db.ForeignKey('employee.employeeID'))
    before_images = db.Column(db.String(500))  # file path e.g. '/uploads/bookings/123/before.jpg'
    after_images = db.Column(db.String(500))  # file path e.g. '/uploads/bookings/123/after.jpg'
    job_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    # Methods
    def confirm(self):
        # Confirms the booking
        self.booking_status = 'confirmed'
        db.session.commit()

    def reschedule(self, new_start_time, new_end_time):
        # Reschedules the booking to a new time
        self.start_time = new_start_time
        self.end_time = new_end_time
        db.session.commit()

    def cancel(self):
        # Cancels the booking
        self.booking_status = 'cancelled'
        db.session.commit()

    def update_job_status(self, new_status):
        # Updates the current status of the job
        self.booking_status = new_status
        db.session.commit()

    def update_block_status(self, is_blocked, block_reason):
        # Blocks or unblocks a time slot with a reason
        self.is_blocked = is_blocked
        self.block_reason = block_reason
        db.session.commit()

    def upload_before_images(self, file_path):
        # Saves the file path of before job images e.g. '/uploads/bookings/123/before.jpg'
        self.before_images = file_path
        db.session.commit()

    def upload_after_images(self, file_path):
        # Saves the file path of after job images e.g. '/uploads/bookings/123/after.jpg'
        self.after_images = file_path
        db.session.commit()