from flask_mail import Mail, Message
from flask import current_app

mail = Mail()

class NotificationService:

    def send_booking_confirmation(self, booking):
        # Emails customer their booking details
        msg = Message(
            subject='Booking Confirmation - Xpair Detailing',
            recipients=[booking.customer.email],
            body=f'Your booking has been confirmed for {booking.date} at {booking.start_time}.'
        )
        mail.send(msg)

    def send_booking_cancellation(self, booking):
        # Notifies customer and employee of cancellation
        msg = Message(
            subject='Booking Cancelled - Xpair Detailing',
            recipients=[booking.customer.email],
            body=f'Your booking on {booking.date} has been cancelled.'
        )
        mail.send(msg)

    def send_availability_approved(self, availability_record):
        # Notifies employee their availability was approved
        msg = Message(
            subject='Availability Approved - Xpair Detailing',
            recipients=[availability_record.employee.email],
            body=f'Your availability for {availability_record.day} has been approved.'
        )
        mail.send(msg)

    def send_availability_changes_requested(self, availability_record):
        # Notifies employee manager requested changes
        msg = Message(
            subject='Availability Changes Requested - Xpair Detailing',
            recipients=[availability_record.employee.email],
            body=f'Your availability for {availability_record.day} needs changes. Manager notes: {availability_record.manager_notes}'
        )
        mail.send(msg)

    def send_schedule_published(self, periodID):
        # Notifies all employees their schedule is live
        from src.employee import Employee
        employees = Employee.query.all()
        for employee in employees:
            msg = Message(
                subject='Schedule Published - Xpair Detailing',
                recipients=[employee.email],
                body=f'The official schedule for period {periodID} has been published.'
            )
            mail.send(msg)

    def send_assignment_notification(self, booking):
        # Notifies employee they have been assigned to a job
        msg = Message(
            subject='New Job Assignment - Xpair Detailing',
            recipients=[booking.assigned_employee.email],
            body=f'You have been assigned to a job on {booking.date} at {booking.start_time}.'
        )
        mail.send(msg)