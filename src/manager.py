from .database import db
from .person import Person
from .availability_record import AvailabilityRecord
from .booking import Booking
from .service import Service


class Manager(Person):
    # Inherits from Person
    __tablename__ = 'manager'

    # Variables
    managerID = db.Column(db.Integer, db.ForeignKey('person.id'), primary_key=True)
    capacity_rule_id = db.Column(db.Integer, nullable=True)
    max_car_capacity = db.Column(db.Integer, nullable=True)
    
    # Polymetric identity which essentially identifies this class as a part of the Person class
    __mapper_args__ = {
        'polymorphic_identity': 'manager',
    }

    # Methods
    def approve_availability(self, availabilityID) -> bool:
        # Approves an employee's availability record
        record = AvailabilityRecord.query.get(availabilityID)
        if not record:
            raise ValueError(f"AvailabilityRecord with ID {availabilityID} not found.")
        record.mark_approved()
        record.managerID = self.managerID  # Link this manager as the reviewer
        db.session.commit()

        # Triggers email notification
        from .notification_service import NotificationService
        NotificationService().notify(recipient=record.employee, event='availability_approved', occupant=record)
        
        return True
    
    def request_changes(self, availabilityID, notes) -> bool:
        # Requests changes to an employee's availability record
        record = AvailabilityRecord.query.get(availabilityID)
        if not record:
            raise ValueError(f"AvailabilityRecord with ID {availabilityID} not found.")
        record.mark_changes_requested(notes)
        record.managerID = self.managerID  # Link this manager as the reviewer
        db.session.commit()

        # Triggers email notification
        from .notification_service import NotificationService
        NotificationService().notify(recipient=record.employee, event='availability_changes_requested', occupant=record)
        
        return True

    def enforce_capacity_rule(self, capacity_rule_id, max_car_capacity):
        # Sets the maximum number of cars allowed per day
        self.capacity_rule_id = capacity_rule_id
        self.max_car_capacity = max_car_capacity
        db.session.commit()

        return True

    def block_time_slot(self, block_reason, start_time, end_time):
        # Blocks a time slot so it cannot be booked.
        # customerID, serviceID, and vehicleID are set to None for manager-blocked slots;
        # those columns must be nullable=True in the Booking model to support this.
        from datetime import datetime
        slot = Booking(
            periodID=None,
            date=start_time.date() if isinstance(start_time, datetime) else start_time,
            start_time=start_time,
            end_time=end_time,
            is_available=False,
            is_blocked=True,
            block_reason=block_reason,
            booking_status='blocked',
            customerID=None,
            serviceID=None,
            vehicleID=None,
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

        return True

    def configure_add_on_options(self, serviceID, available_add_ons):
        # Updates the available add-ons for a service
        service = Service.query.get(serviceID)
        if not service:
            raise ValueError(f"Service with ID {serviceID} not found.")
        service.available_add_ons = available_add_ons
        db.session.commit()

        return True

    def validate_schedule_conflicts(self, periodID):
        # Checks for scheduling conflicts in a given work week
        
        # Orders bookings chronologically to group employee schedules together
        bookings = Booking.query.filter_by(periodID=periodID).order_by(
            Booking.assigned_employee, Booking.start_time
        ).all()

        conflicts = []
        # Compares every booking against every following one to check for overlaps
        for i in range(len(bookings)):
            for j in range(i + 1, len(bookings)):
                a, b = bookings[i], bookings[j]
                # If the bookings belong to different employees = no conflict
                if a.assigned_employee != b.assigned_employee:
                    continue
                # Checks if start time of booking A starts before booking B ends and vice-versa
                if a.start_time < b.end_time and b.start_time < a.end_time:
                    conflicts.append((a.bookingID, b.bookingID))
        return conflicts

    def publish_official_schedule(self, periodID):
        # Publishes the official schedule by confirming all pending bookings for the period
        bookings = Booking.query.filter_by(periodID=periodID, booking_status='pending').all()
        for booking in bookings:
            booking.booking_status = 'confirmed'
        db.session.commit()

        # Triggers email notification
        from .notification_service import NotificationService
        NotificationService().notify(recipient=None, event='schedule_published', occupant=periodID)
        
        return len(bookings)
    
    
    def force_change_appointment_time(self, bookingID, start_time, end_time):
        # Forces a reschedule of a booking to new start and end times
        booking = Booking.query.get(bookingID)
        if not booking:
            raise ValueError(f"Booking with ID {bookingID} not found.")
        booking.reschedule(start_time, end_time)

        return True

    def process_cancellation(self, bookingID) -> bool:
        # Cancels a booking on behalf of the manager
        booking = Booking.query.get(bookingID)
        if not booking:
            raise ValueError(f"Booking with ID {bookingID} not found.")
        booking.cancel()
        
        return True

    def finalize_and_save_schedule(self, periodID):
        # Validates there are no conflicts, then publishes the schedule
        conflicts = self.validate_schedule_conflicts(periodID)
        if conflicts:
            raise ValueError(
                f"Cannot finalize schedule: {len(conflicts)} conflict(s) found. "
                f"Conflicting booking pairs: {conflicts}"
            )
        self.publish_official_schedule(periodID)

        return True

    def generate_report(self, periodID) -> list:
        # Generates a performance report for a given work week
        # Returns a list of metric entries; Dashboard handles display
        bookings = Booking.query.filter_by(periodID=periodID).all()
        total = len(bookings)
        completed = sum(1 for b in bookings if b.booking_status == 'completed')
        cancelled = sum(1 for b in bookings if b.booking_status == 'cancelled')
        confirmed = sum(1 for b in bookings if b.booking_status == 'confirmed')
        pending   = sum(1 for b in bookings if b.booking_status == 'pending')

        return [
            {'metric': 'periodID',         'value': periodID},
            {'metric': 'total_bookings',   'value': total},
            {'metric': 'completed',        'value': completed},
            {'metric': 'cancelled',        'value': cancelled},
            {'metric': 'confirmed',        'value': confirmed},
            {'metric': 'pending',          'value': pending},
            {'metric': 'completion_rate',  'value': round((completed / total * 100), 2) if total > 0 else 0},
        ]

    def retrieve_system_data(self) -> dict:
        # Retrieves system-wide data for the dashboard.
        # Returns a keyed dict so Dashboard.calculate_analytics() can consume it correctly.
        from .employee import Employee
        from .customer import Customer

        return {
            'bookings':  Booking.query.all(),
            'employees': Employee.query.all(),
            'customers': Customer.query.all(),
            'services':  Service.query.all(),
        }

    def assign_employee(self, bookingID, employeeID):
        # Assigns an employee to a booking
        booking = Booking.query.get(bookingID)
        if not booking:
            raise ValueError(f"Booking with ID {bookingID} not found.")
        booking.assigned_employee = employeeID
        db.session.commit()

        return True

        # Triggers email notification
        from .employee import Employee
        assigned_emp = Employee.query.get(employeeID)
        from .notification_service import NotificationService
        NotificationService().notify(recipient=assigned_emp, event='job_assigned', occupant=booking)