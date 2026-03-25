from flask_mail import Message
from app import mail

class NotificationService:
    # A generalized utility class for handling all system notifications via Pub-Sub pattern.

    def notify_stakeholders(self, event: str, recipient=None, payload=None):
        """
        event: String identifier for the notification type.
        recipient: The Person object (Customer, Employee) receiving the email. Can be None for mass emails.
        payload: The object tied to the event (e.g., Booking object, AvailabilityRecord object, or a Dictionary).
        """
        subject = ""
        body = ""
        recipients_list = []

        # ---------------------------------------------------------
        # 1. CUSTOMER EVENTS
        # ---------------------------------------------------------
        if event == 'booking_confirmed':
            subject = 'Booking Confirmation - Xpair Detailing'
            body = f'Your booking has been confirmed for {payload.date} at {payload.start_time}.'
            recipients_list = [recipient.email]

        elif event == 'booking_cancelled':
            subject = 'Booking Cancelled - Xpair Detailing'
            body = f'Your booking on {payload.date} has been cancelled.'
            recipients_list = [recipient.email]

        # ---------------------------------------------------------
        # 2. EMPLOYEE EVENTS
        # ---------------------------------------------------------
        elif event == 'availability_approved':
            subject = 'Availability Approved - Xpair Detailing'
            body = f'Your availability for {payload.day} has been approved.'
            recipients_list = [recipient.email]

        elif event == 'availability_changes_requested':
            subject = 'Availability Changes Requested - Xpair Detailing'
            body = f'Your availability for {payload.day} needs changes. Manager notes: {payload.manager_notes}'
            recipients_list = [recipient.email]

        elif event == 'job_assigned':
            subject = 'New Job Assignment - Xpair Detailing'
            body = f'You have been assigned to a job on {payload.date} at {payload.start_time}.'
            recipients_list = [recipient.email]

        elif event == 'schedule_published':
            # Mass email: No single recipient passed in. We query all employees.
            from src.employee import Employee
            employees = Employee.query.all()
            recipients_list = [emp.email for emp in employees]
            
            subject = 'Schedule Published - Xpair Detailing'
            body = f'The official schedule for period {payload} has been published.'

        # ---------------------------------------------------------
        # 3. MANAGER EVENTS
        # ---------------------------------------------------------
        elif event == 'manager_alert':
            # Mass email: Alert all managers. Payload is a dictionary containing the booking and the message.
            from src.manager import Manager
            managers = Manager.query.all()
            recipients_list = [mgr.email for mgr in managers]
            
            booking = payload.get('booking')
            alert_message = payload.get('message')
            
            subject = f'URGENT: Job #{booking.bookingID} Update'
            body = f'The job on {booking.date} for {booking.customer.first_name} requires your attention. \nMessage: {alert_message}'

        # ---------------------------------------------------------
        # EXECUTE EMAIL SEND
        # ---------------------------------------------------------
        if recipients_list:
            msg = Message(subject=subject, recipients=recipients_list, body=body)
            mail.send(msg)