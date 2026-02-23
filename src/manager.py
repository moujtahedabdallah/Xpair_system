from .database import db
from .person import Person
from .availability_record import AvailabilityRecord
from .booking import Booking
from .service import Service


class Manager(Person):
    __tablename__ = 'manager'

    # Variables
    managerID = db.Column(db.Integer, db.ForeignKey('person.id'), primary_key=True)
    capacity_rule_id = db.Column(db.Integer, nullable=True)
    max_car_capacity = db.Column(db.Integer, nullable=True)
    
    __mapper_args__ = {
        'polymorphic_identity': 'manager',
    }

    # Methods
    def approve_availability(self, availabilityID):
        # Approves an employee's availability record
        record = AvailabilityRecord.query.get(availabilityID)
        if not record:
            raise ValueError(f"AvailabilityRecord with ID {availabilityID} not found.")
        record.mark_approved()
        record.reviewed_by = self.managerID
        db.session.commit()

    def request_changes(self, availabilityID, notes):
        # Requests changes to an employee's availability record
        record = AvailabilityRecord.query.get(availabilityID)
        if not record:
            raise ValueError(f"AvailabilityRecord with ID {availabilityID} not found.")
        record.mark_changes_requested(notes)
        record.reviewed_by = self.managerID
        db.session.commit()

    def enforce_capacity_rule(self, capacity_rule_id, max_car_capacity):
        # Sets the maximum number of cars allowed per day
        self.capacity_rule_id = capacity_rule_id
        self.max_car_capacity = max_car_capacity
        db.session.commit()

    def block_time_slot(self, block_reason, start_time, end_time):
        # Blocks a time slot so it cannot be booked
        from datetime import datetime
        slot = Booking(
            periodID=None,
            date=start_time.date() if isinstance(start_time, datetime) else start_time,
            start_time=start_time,
            end_time=end_time,
            is_available=False,
            is_blocked=True,
            block_reason=block_reason,
            booking_status='blocked'
        )
        db.session.add(slot)
        db.session.commit()
        return slot

    def update_service_price(self, serviceID, base_price):
        # Updates the base price of a service
        service = Service.query.get(serviceID)
        if not service:
            raise ValueError(f"Service with ID {serviceID} not found.")
        service.base_price = base_price
        db.session.commit()

    def configure_add_on_options(self, serviceID, available_add_ons):
        # Updates the available add-ons for a service
        service = Service.query.get(serviceID)
        if not service:
            raise ValueError(f"Service with ID {serviceID} not found.")
        service.available_add_ons = available_add_ons
        db.session.commit()

    def validate_schedule_conflicts(self, periodID):
        # Checks for scheduling conflicts in a given work week
        # Returns a list of conflicting booking ID pairs (same employee, overlapping times)
        bookings = Booking.query.filter_by(periodID=periodID).order_by(
            Booking.assigned_employee, Booking.start_time
        ).all()

        conflicts = []
        for i in range(len(bookings)):
            for j in range(i + 1, len(bookings)):
                a, b = bookings[i], bookings[j]
                if a.assigned_employee != b.assigned_employee:
                    continue
                if a.start_time < b.end_time and b.start_time < a.end_time:
                    conflicts.append((a.bookingID, b.bookingID))
        return conflicts

    def publish_official_schedule(self, periodID):
        # Publishes the official schedule by confirming all pending bookings for the period
        bookings = Booking.query.filter_by(periodID=periodID, booking_status='pending').all()
        for booking in bookings:
            booking.booking_status = 'confirmed'
        db.session.commit()
        return len(bookings)

    def force_change_appointment_time(self, bookingID, start_time, end_time):
        # Forces a reschedule of a booking to new start and end times
        booking = Booking.query.get(bookingID)
        if not booking:
            raise ValueError(f"Booking with ID {bookingID} not found.")
        booking.reschedule(start_time, end_time)

    def process_cancellation(self, bookingID):
        # Cancels a booking on behalf of the manager
        booking = Booking.query.get(bookingID)
        if not booking:
            raise ValueError(f"Booking with ID {bookingID} not found.")
        booking.cancel()

    def finalize_and_save_schedule(self, periodID):
        # Validates there are no conflicts, then publishes the schedule
        conflicts = self.validate_schedule_conflicts(periodID)
        if conflicts:
            raise ValueError(
                f"Cannot finalize schedule: {len(conflicts)} conflict(s) found. "
                f"Conflicting booking pairs: {conflicts}"
            )
        self.publish_official_schedule(periodID)

    def generate_report(self, periodID):
        # Generates a performance report for a given work week
        bookings = Booking.query.filter_by(periodID=periodID).all()
        total = len(bookings)
        completed = sum(1 for b in bookings if b.booking_status == 'completed')
        cancelled = sum(1 for b in bookings if b.booking_status == 'cancelled')
        confirmed = sum(1 for b in bookings if b.booking_status == 'confirmed')
        pending   = sum(1 for b in bookings if b.booking_status == 'pending')

        return {
            'periodID': periodID,
            'total_bookings': total,
            'completed': completed,
            'cancelled': cancelled,
            'confirmed': confirmed,
            'pending': pending,
            'completion_rate': round((completed / total * 100), 2) if total > 0 else 0,
        }

    def retrieve_system_data(self):
        # Retrieves system-wide data for the dashboard
        from .employee import Employee
        from .customer import Customer

        return {
            'bookings': Booking.query.all(),
            'employees': Employee.query.all(),
            'customers': Customer.query.all(),
            'services': Service.query.all(),
        }

    def assign_employee(self, bookingID, employeeID):
        # Assigns an employee to a booking
        booking = Booking.query.get(bookingID)
        if not booking:
            raise ValueError(f"Booking with ID {bookingID} not found.")
        booking.assigned_employee = employeeID
        db.session.commit()