import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, session
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

    all_services = Service.query.all()
    return render_template('index.html', services=all_services)


@app.route('/book', methods=['GET', 'POST'])
def booking_page():

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
        # 1. Extract guest data only if not logged in as customer
        if session.get('user_role') == 'customer':
            f_name = l_name = email = phone = None
        else:
            f_name = request.form.get('first_name')
            l_name = request.form.get('last_name')
            email  = request.form.get('email')
            phone  = request.form.get('phone')

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

        # 4. Handle Customer record
        if session.get('user_role') == 'customer':
            customer = Customer.query.get(session['user_id'])
        else:
            customer = Customer.query.filter_by(email=email).first()
            if not customer:
                customer = Customer(
                    first_name=f_name,
                    last_name=l_name,
                    email=email,
                    phone=phone,
                    password=generate_password_hash("guest_placeholder_123"),
                    role="customer",
                    address="Guest Checkout"
                )
                db.session.add(customer)
                db.session.commit()

        # 5. Handle Vehicle record
        new_vehicle = None

        if session.get('user_role') == 'customer' and customer.vehicle_id:
            new_vehicle = Vehicle.query.get(customer.vehicle_id)
            if new_vehicle:
                new_vehicle.update_size(vehicle_size)
            else:
                # vehicle_id was stale — clear it so the else block runs
                customer.vehicle_id = None

        if new_vehicle is None:
            phone_suffix = phone[-4:] if phone else "0000"
            unique_plate = f"GUEST-{phone_suffix}-{datetime.now().strftime('%S')}"
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

@app.route("/demo/employee", methods=["GET"])
def demo_employee_redirect():
    """
    Redirect to the first Employee found in the DB (demo mode).
    """
    employee = Employee.query.order_by(Employee.employeeID.asc()).first()
    if not employee:
        flash("No employees exist yet. Run seed_data.py (or create an employee) to view UC5.", "danger")
        return redirect(url_for("home"))
    return redirect(url_for("employee_jobs", employee_id=employee.employeeID))


@app.route("/demo/manager", methods=["GET"])
def demo_manager_redirect():
    """
    Redirect to the first Manager found in the DB (demo mode).
    """
    manager = Manager.query.order_by(Manager.managerID.asc()).first()
    if not manager:
        flash("No managers exist yet. Run seed_data.py (or create a manager) to view UC7.", "danger")
        return redirect(url_for("home"))
    return redirect(url_for("manager_availability", manager_id=manager.managerID))

# --- UC1: AUTH ROUTES (Login / Signup / Logout / Vehicle Info) ---

from werkzeug.security import generate_password_hash

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Route: Login Page (Use Case 1)
    GET:  Renders the login form (Customer or Staff tab).
    POST: Authenticates via Person.authenticate_user() (checks hashed password),
          sets session, redirects by role.
    """
    if request.method == 'POST':
        role_tab   = request.form.get('role_tab')
        email      = request.form.get('email', '').strip().lower()
        password   = request.form.get('password', '').strip()
        department = request.form.get('department', '')

        if role_tab == 'customer':
            user = Customer.query.filter_by(email=email).first()
            if user and user.authenticate_user(password):
                session['user_id']   = user.customerID
                session['user_role'] = 'customer'
                session['user_name'] = user.first_name
                # Customer login success — add this line before the redirect
                flash("Welcome back to Xpair Detailing!", "success")
                return redirect(url_for('home'))
            flash("Invalid email or password.", "danger")
            return redirect(url_for('login'))

        else:  # staff tab
            if department == 'management':
                user = Manager.query.filter_by(email=email).first()
                if user and user.authenticate_user(password):
                    session['user_id']   = user.managerID
                    session['user_role'] = 'manager'
                    session['user_name'] = user.first_name
                    # Manager login success — add before redirect
                    flash("Welcome back to Xpair Detailing!", "success")
                    return redirect(url_for('manager_availability', manager_id=user.managerID))
                flash("Invalid email, password, or department.", "danger")
                return redirect(url_for('login'))

            elif department == 'employee':
                user = Employee.query.filter_by(email=email).first()
                if user and user.authenticate_user(password):
                    session['user_id']   = user.employeeID
                    session['user_role'] = 'employee'
                    session['user_name'] = user.first_name
                    # Employee login success — add before redirect
                    flash("Welcome back to Xpair Detailing!", "success")
                    return redirect(url_for('employee_jobs', employee_id=user.employeeID))
                flash("Invalid email, password, or department.", "danger")
                return redirect(url_for('login'))

            else:
                flash("Please select a department.", "danger")
                return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
   
    if request.method == 'POST':
        role_tab   = request.form.get('role_tab')
        f_name = request.form.get('first_name', '').strip()
        l_name = request.form.get('last_name', '').strip()
        email      = request.form.get('email', '').strip().lower()
        phone      = request.form.get('phone', '').strip()
        password   = request.form.get('password', '').strip()
        confirm_pw = request.form.get('confirm_password', '').strip()
        department = request.form.get('department', '')

        # Validation
        if password != confirm_pw:
            flash("Passwords do not match.", "danger")
            return redirect(url_for('signup'))

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
            return redirect(url_for('signup'))


        hashed_pw = generate_password_hash(password)

        if role_tab == 'customer':
            if Customer.query.filter_by(email=email).first():
                flash("An account with that email already exists.", "danger")
                return redirect(url_for('signup'))

            new_user = Customer(
                first_name=f_name,
                last_name=l_name,
                email=email,
                phone=phone,
                password=hashed_pw,
                role='customer',
                address=''
            )
            # create_profile() handles db.session.add, commit, and welcome email
            new_user.create_profile()
            flash("Account created! Welcome to Xpair Detailing.", "success")


            session['user_id']   = new_user.customerID
            session['user_role'] = 'customer'
            session['user_name'] = new_user.first_name
            return redirect(url_for('vehicle_info', customer_id=new_user.customerID))

        elif role_tab == 'staff':
            if not department:
                flash("Please select a department.", "danger")
                return redirect(url_for('signup'))

            if department == 'employee':
                if Employee.query.filter_by(email=email).first():
                    flash("An account with that email already exists.", "danger")
                    return redirect(url_for('signup'))

                new_user = Employee(
                    first_name=f_name,
                    last_name=l_name,
                    email=email,
                    phone=phone,
                    password=hashed_pw,
                    role='employee',
                    experience_level='junior',
                    position='Detailer',
                    salary=18.50,
                    working_hours=40.0
                )
                new_user.create_profile()
                flash("Account created! Welcome to Xpair Detailing.", "success")


                session['user_id']   = new_user.employeeID
                session['user_role'] = 'employee'
                session['user_name'] = new_user.first_name
                return redirect(url_for('employee_jobs', employee_id=new_user.employeeID))

            elif department == 'management':
                if Manager.query.filter_by(email=email).first():
                    flash("An account with that email already exists.", "danger")
                    return redirect(url_for('signup'))

                new_user = Manager(
                    first_name=f_name,
                    last_name=l_name,
                    email=email,
                    phone=phone,
                    password=hashed_pw,
                    max_car_capacity=5
                )
                new_user.create_profile()
                flash("Account created! Welcome to Xpair Detailing.", "success")

                session['user_id']   = new_user.managerID
                session['user_role'] = 'manager'
                session['user_name'] = new_user.first_name
                return redirect(url_for('manager_availability', manager_id=new_user.managerID))

    return render_template('signup.html')


@app.route('/vehicle-info/<int:customer_id>', methods=['GET', 'POST'])
def vehicle_info(customer_id):
    """
    Route: Post-Signup Vehicle Info (Use Case 1 — Customer only, optional)
    POST: Uses Customer.add_vehicle() to create and link the Vehicle record,
          then updates customer.vehicle_id to the newly created vehicle.
          'Skip for Now' bypasses the DB write entirely.
    """
    customer = Customer.query.get_or_404(customer_id)

    if request.method == 'POST':
        skip = request.form.get('skip')

        if not skip:
            make  = request.form.get('make', '').strip()
            model = request.form.get('model', '').strip()
            year  = request.form.get('year', '').strip()
            plate = request.form.get('plate', '').strip()
            size  = request.form.get('size', 'medium').strip()

            if make and model and year and plate:
                try:
                    # Delegates to Customer.add_vehicle() which handles Vehicle
                    # creation and links it via customerID
                    new_vehicle = customer.add_vehicle(
                        make=make,
                        model=model,
                        year=int(year),
                        plate=plate,
                        size=size,
                        type='Car'
                    )
                    # Track this as the customer's active vehicle
                    customer.vehicle_id = new_vehicle.vehicleID
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    flash(f"Could not save vehicle: {str(e)}", "danger")
                    return redirect(url_for('vehicle_info', customer_id=customer_id))

        return redirect(url_for('home'))

    return render_template('vehicle_info.html', customer=customer)


@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('home'))

# --- EDIT PROFILE ---

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if not session.get('user_id'):
        flash("Please log in to view your profile.", "danger")
        return redirect(url_for('login'))

    role = session.get('user_role')

    if role == 'customer':
        user = Customer.query.get_or_404(session['user_id'])
    elif role == 'employee':
        user = Employee.query.get_or_404(session['user_id'])
    elif role == 'manager':
        user = Manager.query.get_or_404(session['user_id'])
    else:
        return redirect(url_for('login'))

    if request.method == 'POST':
        # --- Personal Info ---
        f_name = request.form.get('first_name', '').strip()
        l_name = request.form.get('last_name', '').strip()
        email  = request.form.get('email', '').strip().lower()
        phone  = request.form.get('phone', '').strip()

        user.update_first_name(f_name)
        user.update_last_name(l_name)
        user.update_email(email)
        user.update_phone(phone)
        session['user_name'] = f_name

        # --- Vehicle Info (customer only) ---
        if role == 'customer':
            make  = request.form.get('make', '').strip()
            model = request.form.get('v_model', '').strip()
            year  = request.form.get('year', '').strip()
            plate = request.form.get('plate', '').strip()
            size  = request.form.get('size', 'medium')

            if make and model and year and plate:
                try:
                    if user.vehicle_id:
                        vehicle = Vehicle.query.get(user.vehicle_id)
                        if vehicle:
                            vehicle.update_make(make)
                            vehicle.update_model(model)
                            vehicle.update_year(int(year))
                            vehicle.update_plate(plate)
                            vehicle.update_size(size)
                    else:
                        new_vehicle = user.add_vehicle(
                            make=make, model=model,
                            year=int(year), plate=plate,
                            size=size, type='Car'
                        )
                        user.vehicle_id = new_vehicle.vehicleID
                        db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    flash(f"Vehicle update failed: {str(e)}", "danger")
                    return redirect(url_for('profile'))

        # --- Password Change ---
        current_pw = request.form.get('current_password', '').strip()
        new_pw     = request.form.get('new_password', '').strip()
        confirm_pw = request.form.get('confirm_password', '').strip()

        if current_pw and new_pw:
            if not user.authenticate_user(current_pw):
                flash("Current password is incorrect.", "danger")
                return redirect(url_for('profile'))
            if new_pw != confirm_pw:
                flash("New passwords do not match.", "danger")
                return redirect(url_for('profile'))
            if len(new_pw) < 6:
                flash("New password must be at least 6 characters.", "danger")
                return redirect(url_for('profile'))
            user.update_password(new_pw)

        flash("Profile updated successfully.", "success")
        return redirect(url_for('profile'))

    # GET: fetch vehicle for customer
    vehicle = None
    if role == 'customer' and user.vehicle_id:
        vehicle = Vehicle.query.get(user.vehicle_id)

    return render_template('edit_profile.html', user=user, vehicle=vehicle, role=role)

if __name__ == "__main__":
    app.run(debug=True, port=5000)