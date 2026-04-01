import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mail import Mail
from src.database import db

# Import your Problem Domain models from the /src folder
from src.person import Person
from src.vehicle import Vehicle
from src.service import Service
from src.booking import Booking
from src.availability_record import AvailabilityRecord
from src.customer import Customer
from src.employee import Employee
from src.manager import Manager

# Load environment variables (like email passwords) securely from .env
load_dotenv()

app = Flask(__name__)

# --- CONFIGURATION ---
# Database: SQLite file will be created in the /instance folder (Flask default)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///xpair_detailing.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Email: Configuration for automated notifications
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = 'noreply@xpairdetailing.com'
app.config['MAIL_SUPPRESS_SEND'] = True  # This "mutes" the email but keeps the app running

# Security: Required for Flask to handle session-based "Flash" messages
app.config['SECRET_KEY'] = 'xpair_secret_key_2026'


# --- INITIALIZATION ---
mail = Mail()
db.init_app(app)
mail.init_app(app)

# Create database tables automatically based on your /src models
with app.app_context():
    try:
        db.create_all()
        print("✅ SUCCESS: Database linked and tables created!")
    except Exception as e:
        print(f"❌ ERROR: Database sync failed: {e}")


# --- ROUTES ---

@app.route('/')
def home():
    """
    Route: Landing Page (Homepage)
    Displays the "Xpair Detailing" hero and loops through the service catalog.
    """
    all_services = Service.query.all()
    return render_template('index.html', services=all_services)


@app.route('/book', methods=['GET', 'POST'])
def booking_page():
    """
    Route: Booking Engine (Use Case 3)
    GET: Displays the interactive Figma-style booking form.
    POST: Processes the submission, creates a Customer/Vehicle, and saves the Booking.
    """

    # --- HANDLING PAGE LOAD (GET) ---
    if request.method == 'GET':
        all_services = Service.query.all()

        # This dictionary is used to populate the Add-ons list in book.html
        add_ons = {
            "UV Protection for Plastics": 25.00,
            "Detailed Seat Cleaning": 60.00,
            "Deep Carpet and Floor Cleaning": 70.00,
            "Water-Repellent Product for Carpets": 30.00,
            "Leather Seat Conditioner": 40.00,
            "Xpair Detailing Air Freshener": 10.00,
            "Odor Neutralizer": 50.00,
            "Black Surface Restoration (Tires)": 35.00,
            "Black Surface Restoration (Plastics)": 40.00
        }

        return render_template('book.html', services=all_services, addons=add_ons)

    # --- HANDLING FORM SUBMISSION (POST) ---
    if request.method == 'POST':
        # 1. Extract Guest/Customer Data from Form
        f_name = request.form.get('first_name')
        l_name = request.form.get('last_name')
        email = request.form.get('email')
        phone = request.form.get('phone')

        # 2. Extract Booking Details
        service_id = int(request.form.get('serviceID'))
        vehicle_size = request.form.get('vehicleSize').lower()  # Sync with src validation
        date_str = request.form.get('date')  # From Flatpickr
        time_str = request.form.get('time')  # From our grid selection
        instructions = request.form.get('notes')

        # Capture Add-ons list and join into a comma-separated string
        addons_list = request.form.getlist('addons')

        # 3. Handle Time Logic (Converting strings to Python DateTime objects)
        try:
            # Combine Date and Time strings (e.g., "2026-03-30 9:00 AM")
            start_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %I:%M %p")

            # Fetch the service to calculate the correct end_time
            selected_service = db.session.get(Service, service_id)
            end_dt = start_dt + timedelta(minutes=selected_service.service_duration)
        except Exception as e:
            flash(f"Invalid Date or Time selection: {e}", "danger")
            return redirect(url_for('booking_page'))

        # 4. Integrate UC1: Handle Customer/Person record
        customer = Customer.query.filter_by(email=email).first()

        if not customer:
            customer = Customer(
                first_name=f_name,
                last_name=l_name,
                email=email,
                phone=phone,
                password="guest_placeholder_123",
                role="customer",
                address="Guest Checkout"
            )
            db.session.add(customer)
            db.session.commit()

        # 5. Handle Vehicle record
        unique_plate = f"GUEST-{phone[-4:]}-{datetime.now().strftime('%S')}"

        new_vehicle = Vehicle(
            make="Guest",
            model="Vehicle",
            year=2026,
            plate=unique_plate,
            type="Car",
            size=vehicle_size,
            customerID=customer.customerID
        )
        db.session.add(new_vehicle)
        db.session.commit()

        # Update the customer's vehicle_id to track this latest vehicle
        customer.vehicle_id = new_vehicle.vehicleID
        db.session.commit()

        # 6. Integrate UC3: Create the Booking Object
        new_booking = Booking(
            customerID=customer.customerID,
            serviceID=service_id,
            vehicleID=new_vehicle.vehicleID,
            date=start_dt.date(),
            start_time=start_dt,
            end_time=end_dt,
            booking_status='pending',
            job_notes=instructions
        )

        try:
            db.session.add(new_booking)
            db.session.flush()
            new_booking.generate_booking_summary(selected_add_ons=addons_list)
            db.session.commit()

            return redirect(url_for('booking_success', booking_id=new_booking.bookingID))

        except Exception as e:
            db.session.rollback()
            flash(f"Database Error: {str(e)}", "danger")
            return redirect(url_for('booking_page'))


# --- ROUTES FOR MANAGE/RESCHEDULE/CANCEL ---

@app.route('/booking-success/<int:booking_id>')
def booking_success(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    return render_template('booking_success.html', booking=booking)

@app.route('/manage/<int:booking_id>')
def manage_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    return render_template('manage_booking.html', booking=booking)

@app.route('/cancel/<int:booking_id>', methods=['POST'])
def cancel_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    booking.cancel()
    flash("Your booking has been successfully cancelled.", "info")
    return redirect(url_for('home'))

@app.route('/reschedule/<int:booking_id>', methods=['GET', 'POST'])
def reschedule_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)

    if request.method == 'POST':
        new_date_str = request.form.get('date')
        new_time_str = request.form.get('time')

        try:
            new_start = datetime.strptime(f"{new_date_str} {new_time_str}", "%Y-%m-%d %I:%M %p")
            new_end = new_start + timedelta(minutes=booking.service.service_duration)
            booking.reschedule(new_start, new_end)
            flash(f"Your appointment has been rescheduled to {new_date_str} at {new_time_str}.", "success")
            return redirect(url_for('manage_booking', booking_id=booking.bookingID))

        except Exception as e:
            db.session.rollback()
            flash(f"Error rescheduling: {str(e)}", "danger")
            return redirect(url_for('reschedule_booking', booking_id=booking.bookingID))

    return render_template('reschedule.html', booking=booking)


# --- UC5 / UC7 (Demo, no auth) ----------------------------------------------

@app.route("/employee/<int:employee_id>/jobs", methods=["GET"])
def employee_jobs(employee_id: int):
    employee = Employee.query.get_or_404(employee_id)
    jobs = (
        Booking.query
        .filter(Booking.assigned_employee == employee_id)
        .order_by(Booking.booking_status.asc(), Booking.start_time.asc())
        .all()
    )
    return render_template("employee_jobs.html", employee=employee, jobs=jobs)


@app.route("/employee/<int:employee_id>/jobs/<int:booking_id>", methods=["GET"])
def employee_job_details(employee_id: int, booking_id: int):
    employee = Employee.query.get_or_404(employee_id)
    booking = Booking.query.get_or_404(booking_id)

    if booking.assigned_employee != employee_id:
        flash("This job is not assigned to that employee (demo check).", "danger")
        return redirect(url_for("employee_jobs", employee_id=employee_id))

    return render_template("employee_job_details.html", employee=employee, booking=booking)


@app.route("/employee/<int:employee_id>/jobs/<int:booking_id>/status", methods=["POST"])
def employee_update_job_status(employee_id: int, booking_id: int):
    booking = Booking.query.get_or_404(booking_id)
    if booking.assigned_employee != employee_id:
        flash("Not allowed (demo check).", "danger")
        return redirect(url_for("employee_jobs", employee_id=employee_id))

    new_status = (request.form.get("booking_status") or "").strip()
    try:
        booking.update_job_status(new_status)
        flash(f"Job status updated to '{new_status}'.", "success")
    except Exception as e:
        db.session.rollback()
        flash(str(e), "danger")

    return redirect(url_for("employee_job_details", employee_id=employee_id, booking_id=booking_id))


@app.route("/employee/<int:employee_id>/jobs/<int:booking_id>/notes", methods=["POST"])
def employee_add_job_notes(employee_id: int, booking_id: int):
    booking = Booking.query.get_or_404(booking_id)
    if booking.assigned_employee != employee_id:
        flash("Not allowed (demo check).", "danger")
        return redirect(url_for("employee_jobs", employee_id=employee_id))

    notes = (request.form.get("job_notes") or "").strip()
    try:
        booking.validate_notes(notes)
        booking.job_notes = notes
        db.session.commit()
        flash("Notes saved.", "success")
    except Exception as e:
        db.session.rollback()
        flash(str(e), "danger")

    return redirect(url_for("employee_job_details", employee_id=employee_id, booking_id=booking_id))


@app.route("/manager/<int:manager_id>/availability", methods=["GET"])
def manager_availability(manager_id: int):
    manager = Manager.query.get_or_404(manager_id)
    submissions = (
        AvailabilityRecord.query
        .order_by(AvailabilityRecord.status.asc(), AvailabilityRecord.created_at.desc())
        .all()
    )
    return render_template("manager_availability_list.html", manager=manager, submissions=submissions)


@app.route("/manager/<int:manager_id>/availability/<int:availability_id>", methods=["GET"])
def manager_availability_details(manager_id: int, availability_id: int):
    manager = Manager.query.get_or_404(manager_id)
    submission = AvailabilityRecord.query.get_or_404(availability_id)
    return render_template("manager_availability_details.html", manager=manager, submission=submission)


@app.route("/manager/<int:manager_id>/availability/<int:availability_id>/approve", methods=["POST"])
def manager_approve_availability(manager_id: int, availability_id: int):
    manager = Manager.query.get_or_404(manager_id)
    try:
        manager.approve_availability(availability_id)
        flash("Availability approved.", "success")
    except Exception as e:
        db.session.rollback()
        flash(str(e), "danger")
    return redirect(url_for("manager_availability", manager_id=manager_id))


@app.route("/manager/<int:manager_id>/availability/<int:availability_id>/request-changes", methods=["POST"])
def manager_request_changes(manager_id: int, availability_id: int):
    manager = Manager.query.get_or_404(manager_id)
    submission = AvailabilityRecord.query.get_or_404(availability_id)

    notes = (request.form.get("manager_notes") or "").strip()
    if not notes:
        flash("Please add notes when requesting changes.", "danger")
        return redirect(url_for("manager_availability_details", manager_id=manager_id, availability_id=availability_id))

    try:
        submission.status = "changes_requested"
        submission.manager_notes = notes
        submission.managerID = manager.managerID
        submission.reviewed_at = datetime.now()
        db.session.commit()
        flash("Changes requested from employee.", "success")
    except Exception as e:
        db.session.rollback()
        flash(str(e), "danger")

    return redirect(url_for("manager_availability", manager_id=manager_id))


if __name__ == "__main__":
    app.run(debug=True, port=5000)