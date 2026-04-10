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
from src.scheduling_period import SchedulingPeriod

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


# INITIALIZATION
mail = Mail()
db.init_app(app)
mail.init_app(app)

# Create database tables automatically based on your /src models (SQLALCHEMY ORM)
with app.app_context():
    try:
        db.create_all()
        print("SUCCESS: Database linked and tables created")
    except Exception as e:
        print(f"ERROR: Database sync failed: {e}")

# ------------------------------------------------------ ALL ROUTES BELOW ------------------------------------------------------

@app.route('/')
def home():
    all_services = Service.query.all()
    return render_template('index.html', services=all_services)

# --- UC3 ROUTES (Booking page logic + handling / Booking success confirmation / Post-booking management (reschedule / cancel) ----------------------------------------------

@app.route('/book', methods=['GET', 'POST'])
def booking_page():

    # --- HANDLING PAGE LOAD ---
    if request.method == 'GET':
        all_services = Service.query.all()

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

    # --- HANDLING FORM SUBMISSION ---
    if request.method == 'POST':
        if session.get('user_role') == 'customer':
            f_name = l_name = email = phone = None
        else:
            f_name = request.form.get('first_name')
            l_name = request.form.get('last_name')
            email  = request.form.get('email')
            phone  = request.form.get('phone')

        service_id   = int(request.form.get('serviceID'))
        vehicle_size = request.form.get('vehicleSize').lower()
        date_str     = request.form.get('date')
        time_str     = request.form.get('time')
        instructions = request.form.get('notes')
        addons_list  = request.form.getlist('addons')

        try:
            start_dt         = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %I:%M %p")
            selected_service = db.session.get(Service, service_id)
            end_dt           = start_dt + timedelta(minutes=selected_service.service_duration)
        except Exception as e:
            flash(f"Invalid Date or Time selection: {e}", "danger")
            return redirect(url_for('booking_page'))

        if session.get('user_role') == 'customer':
            customer = Customer.query.get(session['user_id'])
        else:
            customer = Customer.query.filter_by(email=email).first()
            if not customer:
                customer = Customer(
                    first_name=f_name, last_name=l_name,
                    email=email, phone=phone,
                    password=generate_password_hash("guest_placeholder_123"),
                    role="customer", address="Guest Checkout"
                )
                db.session.add(customer)
                db.session.commit()

        new_vehicle = None

        if session.get('user_role') == 'customer' and customer.vehicle_id:
            new_vehicle = Vehicle.query.get(customer.vehicle_id)
            if new_vehicle:
                new_vehicle.update_size(vehicle_size)
            else:
                customer.vehicle_id = None

        if new_vehicle is None:
            phone_suffix = phone[-4:] if phone else "0000"
            unique_plate = f"GUEST-{phone_suffix}-{datetime.now().strftime('%S')}"
            new_vehicle  = Vehicle(
                make="Guest", model="Vehicle", year=2026,
                plate=unique_plate, type="Car",
                size=vehicle_size, customerID=customer.customerID
            )
            db.session.add(new_vehicle)
            db.session.commit()
            customer.vehicle_id = new_vehicle.vehicleID
            db.session.commit()

        new_booking = Booking(
            customerID=customer.customerID, serviceID=service_id,
            vehicleID=new_vehicle.vehicleID, date=start_dt.date(),
            start_time=start_dt, end_time=end_dt,
            booking_status='pending', job_notes=instructions
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
            new_end   = new_start + timedelta(minutes=booking.service.service_duration)
            booking.reschedule(new_start, new_end)
            flash(f"Your appointment has been rescheduled to {new_date_str} at {new_time_str}.", "success")
            return redirect(url_for('manage_booking', booking_id=booking.bookingID))
        except Exception as e:
            db.session.rollback()
            flash(f"Error rescheduling: {str(e)}", "danger")
            return redirect(url_for('reschedule_booking', booking_id=booking.bookingID))

    return render_template('reschedule.html', booking=booking)


# --- UC5 ROUTES (Demo, no auth) [Job Listing / Job details / Job status updates / Job notes] ----------------------------------------------

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
    booking  = Booking.query.get_or_404(booking_id)

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


# --- UC7 ROUTES (Demo, no auth) [Availability record / Availability details / Approving availability logic / Requesting changes] ----------------------------------------------

@app.route("/manager/<int:manager_id>/availability", methods=["GET"])
def manager_availability(manager_id: int):
    manager     = Manager.query.get_or_404(manager_id)
    submissions = (
        AvailabilityRecord.query
        .order_by(AvailabilityRecord.status.asc(), AvailabilityRecord.created_at.desc())
        .all()
    )
    return render_template("manager_availability_list.html", manager=manager, submissions=submissions)


@app.route("/manager/<int:manager_id>/availability/<int:availability_id>", methods=["GET"])
def manager_availability_details(manager_id: int, availability_id: int):
    manager    = Manager.query.get_or_404(manager_id)
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
    manager    = Manager.query.get_or_404(manager_id)
    submission = AvailabilityRecord.query.get_or_404(availability_id)

    notes = (request.form.get("manager_notes") or "").strip()
    if not notes:
        flash("Please add notes when requesting changes.", "danger")
        return redirect(url_for("manager_availability_details", manager_id=manager_id, availability_id=availability_id))

    try:
        submission.status       = "changes_requested"
        submission.manager_notes = notes
        submission.managerID    = manager.managerID
        submission.reviewed_at  = datetime.now()
        db.session.commit()
        flash("Changes requested from employee.", "success")
    except Exception as e:
        db.session.rollback()
        flash(str(e), "danger")

    return redirect(url_for("manager_availability", manager_id=manager_id))


# --- UC8 ROUTES (Management Dashboard) ----------------------------------------------

@app.route("/manager/<int:manager_id>/dashboard", methods=["GET"])
def manager_dashboard(manager_id: int):
    from datetime import date, timedelta

    # Auth guard
    if session.get('user_role') != 'manager' or session.get('user_id') != manager_id:
        return redirect(url_for('login'))

    manager = Manager.query.get_or_404(manager_id)

    # Period filter (SubFlow S-1)
    selected_period = request.args.get('period', 'all')
    period_labels   = {
        'today': 'Today', 'week': 'This Week',
        'month': 'This Month', 'year': 'This Year', 'all': 'All Time',
    }
    period_label = period_labels.get(selected_period, 'All Time')
    today = date.today()

    if selected_period == 'today':
        date_from, date_to = today, today
    elif selected_period == 'week':
        date_from = today - timedelta(days=today.weekday())
        date_to   = date_from + timedelta(days=6)
    elif selected_period == 'month':
        date_from, date_to = today.replace(day=1), today
    elif selected_period == 'year':
        date_from, date_to = today.replace(month=1, day=1), today
    else:
        date_from = date_to = None

    # Query bookings (Steps 3 & 4)
    query = Booking.query.filter(Booking.is_blocked == False)
    if date_from and date_to:
        query = query.filter(Booking.date >= date_from, Booking.date <= date_to)
    all_bookings = query.all()

    # Alternate flow — insufficient data
    insufficient_data = (selected_period != 'all' and len(all_bookings) == 0)

    # ── KPI CALCULATIONS (Step 5) ──
    billable  = [b for b in all_bookings if b.booking_status != 'cancelled' and b.service]
    revenue   = sum(b.service.base_price for b in billable)
    bookings  = len(all_bookings)
    active    = sum(1 for b in all_bookings if b.booking_status in ('in_progress', 'assigned', 'confirmed', 'pending'))
    completed = sum(1 for b in all_bookings if b.booking_status == 'completed')

    kpis = {
        'revenue':     f'{revenue:,.2f}',
        'bookings':    bookings,
        'active_jobs': active,
        'completed':   completed,
    }

    # ── TREND INDICATORS (vs previous calendar month) ──
    def month_stats(year, month):
        from calendar import monthrange
        last_day = monthrange(year, month)[1]
        first    = date(year, month, 1)
        last     = date(year, month, last_day)
        bks = Booking.query.filter(
            Booking.is_blocked == False,
            Booking.date >= first,
            Booking.date <= last
        ).all()
        rev  = sum(b.service.base_price for b in bks if b.booking_status != 'cancelled' and b.service)
        cnt  = len(bks)
        act  = sum(1 for b in bks if b.booking_status in ('in_progress', 'assigned', 'confirmed', 'pending'))
        comp = sum(1 for b in bks if b.booking_status == 'completed')
        return {'revenue': rev, 'bookings': cnt, 'active': act, 'completed': comp}

    def pct_change(curr, prev):
        if prev == 0:
            return None
        return round(((curr - prev) / prev) * 100)

    curr_month = today.month
    curr_year  = today.year
    prev_month = curr_month - 1 if curr_month > 1 else 12
    prev_year  = curr_year if curr_month > 1 else curr_year - 1

    curr_stats = month_stats(curr_year, curr_month)
    prev_stats = month_stats(prev_year, prev_month)

    trends = {
        'revenue_pct':   pct_change(curr_stats['revenue'],   prev_stats['revenue']),
        'bookings_pct':  pct_change(curr_stats['bookings'],  prev_stats['bookings']),
        'active_pct':    pct_change(curr_stats['active'],    prev_stats['active']),
        'completed_pct': pct_change(curr_stats['completed'], prev_stats['completed']),
    }

    # ── BAR CHART — rolling 6 months, revenue + booking count ──
    monthly_data = []
    for i in range(5, -1, -1):
        month_date = (today.replace(day=1) - timedelta(days=i * 28)).replace(day=1)
        ym_str     = month_date.strftime('%Y-%m')
        month_bks  = Booking.query.filter(
            Booking.is_blocked == False,
            db.func.strftime('%Y-%m', Booking.date) == ym_str
        ).all()
        month_rev  = sum(b.service.base_price for b in month_bks if b.booking_status != 'cancelled' and b.service)
        month_cnt  = len(month_bks)
        monthly_data.append({
            'month':         month_date.strftime('%b'),
            'ym':            ym_str,
            'value':         month_rev,
            'booking_count': month_cnt,
            'active':        ym_str == today.strftime('%Y-%m'),
            'pct':           0,
            'bpct':          0,
        })

    max_rev = max((m['value'] for m in monthly_data), default=1) or 1
    max_cnt = max((m['booking_count'] for m in monthly_data), default=1) or 1
    for m in monthly_data:
        m['pct']  = max(round((m['value']         / max_rev) * 100), 5)
        m['bpct'] = max(round((m['booking_count'] / max_cnt) * 100), 5)

    # ── DONUT — top 4 services with percentage ──
    palette        = ['#D82242', '#1A1D21', '#9CA3AF', '#D1D5DB']
    service_counts = {}
    for b in all_bookings:
        if b.service:
            service_counts[b.service.service_name] = service_counts.get(b.service.service_name, 0) + 1

    total_svc = sum(service_counts.values()) or 1
    by_service = [
        {
            'label': name,
            'count': count,
            'color': palette[i % len(palette)],
            'pct':   round((count / total_svc) * 100),
        }
        for i, (name, count) in enumerate(
            sorted(service_counts.items(), key=lambda x: x[1], reverse=True)[:4]
        )
    ]

    chart_data = {'monthly': monthly_data, 'by_service': by_service}

    # ── RECENT BOOKINGS TABLE with month label for JS filtering ──
    recent_raw = (
        Booking.query
        .filter(Booking.is_blocked == False)
        .order_by(Booking.date.desc(), Booking.start_time.desc())
        .limit(50).all()
    )
    recent_bookings = [
        {
            'id':          b.bookingID,
            'service':     b.service.service_name if b.service else '—',
            'date':        b.date.strftime('%Y-%m-%d'),
            'time':        b.start_time.strftime('%I:%M %p'),
            'status':      b.booking_status,
            'month_label': b.date.strftime('%b'),
        }
        for b in recent_raw
    ]

    return render_template(
        'manager_dashboard.html',
        manager=manager,
        selected_period=selected_period,
        period_label=period_label,
        insufficient_data=insufficient_data,
        kpis=kpis,
        trends=trends,
        chart_data=chart_data,
        recent_bookings=recent_bookings,
    )


# --- CUSTOMER: MY BOOKINGS ROUTE ----------------------------------------------

@app.route('/my-bookings')
def my_bookings():
    if not session.get('user_id') or session.get('user_role') != 'customer':
        flash("Please log in to view your bookings.", "danger")
        return redirect(url_for('login'))

    customer = Customer.query.get_or_404(session['user_id'])
    bookings = (
        Booking.query
        .filter(Booking.customerID == customer.customerID, Booking.is_blocked == False)
        .order_by(Booking.date.desc(), Booking.start_time.desc())
        .all()
    )
    return render_template('my_bookings.html', customer=customer, bookings=bookings)


# --- UC4 ROUTES (Employee Availability Submission) ----------------------------------------------

def build_period_dict(sp, employee_id):
    from datetime import timedelta
    from src.availability_record import AvailabilityRecord

    # Determine display status for this employee
    existing = AvailabilityRecord.query.filter_by(
        periodID=sp.periodID, employeeID=employee_id
    ).first()

    if existing:
        display_status  = 'submitted'
        submitted_on    = existing.created_at.strftime('%b %d, %Y') if existing.created_at else '—'
        review_status   = existing.status.replace('_', ' ').title()
    else:
        display_status  = sp.status
        submitted_on    = None
        review_status   = None

    p = {
        'id':           sp.periodID,
        'label':        sp.label,
        'period_range': f"{sp.start_date.strftime('%b %d')} - {sp.end_date.strftime('%b %d, %Y')}",
        'due_date':     sp.due_date.strftime('%b %d, %Y'),
        'start':        sp.start_date,
        'end':          sp.end_date,
        'status':       display_status,
        'submitted_on': submitted_on,
        'review_status':review_status,
    }

    # Build date list for dropdowns
    dates   = []
    current = sp.start_date
    while current <= sp.end_date:
        dates.append({'value': current.strftime('%Y-%m-%d'), 'label': current.strftime('%a, %b %d')})
        current += timedelta(days=1)
    p['dates'] = dates

    # Build calendar weeks
    start_monday = sp.start_date - timedelta(days=sp.start_date.weekday())
    end_sunday   = sp.end_date + timedelta(days=(6 - sp.end_date.weekday()))
    calendar_weeks, week = [], []
    current = start_monday
    while current <= end_sunday:
        week.append({
            'weekday':   current.strftime('%a'),
            'day_num':   current.day,
            'value':     current.strftime('%Y-%m-%d'),
            'is_period': sp.start_date <= current <= sp.end_date,
            'has_slot':  False,
        })
        if len(week) == 7:
            calendar_weeks.append(week)
            week = []
        current += timedelta(days=1)
    if week:
        calendar_weeks.append(week)
    p['calendar_weeks'] = calendar_weeks

    return p


def get_time_options():
    options = []
    from datetime import datetime, timedelta
    t = datetime(2000, 1, 1, 6, 0)
    while t.hour < 22:
        options.append({'value': t.strftime('%H:%M'), 'label': t.strftime('%I:%M %p')})
        t += timedelta(minutes=30)
    return options


@app.route("/employee/<int:employee_id>/availabilities", methods=["GET"])
def employee_availabilities(employee_id: int):
    employee = Employee.query.get_or_404(employee_id)
    sps      = SchedulingPeriod.query.order_by(SchedulingPeriod.start_date.asc()).all()
    periods  = [build_period_dict(sp, employee_id) for sp in sps]
    return render_template("employee_availabilities.html", employee=employee, periods=periods)


@app.route("/employee/<int:employee_id>/availabilities/<int:period_id>/enter", methods=["GET", "POST"])
def employee_availability_enter(employee_id: int, period_id: int):
    from datetime import datetime
    employee = Employee.query.get_or_404(employee_id)
    sp       = SchedulingPeriod.query.get_or_404(period_id)
    period   = build_period_dict(sp, employee_id)
    if not sp.is_open():
        flash("This scheduling period is not open for submission.", "danger")
        return redirect(url_for("employee_availabilities", employee_id=employee_id))

    # Use session to store slots temporarily
    session_key = f"avail_slots_{employee_id}_{period_id}"
    slots = session.get(session_key, [])

    if request.method == "POST":
        action = request.form.get("action")

        if action == "add":
            date_val   = request.form.get("date", "").strip()
            start_val  = request.form.get("start_time", "").strip()
            end_val    = request.form.get("end_time", "").strip()

            if date_val and start_val and end_val:
                # Validate end > start
                start_dt = datetime.strptime(f"{date_val} {start_val}", "%Y-%m-%d %H:%M")
                end_dt   = datetime.strptime(f"{date_val} {end_val}",   "%Y-%m-%d %H:%M")
                if end_dt <= start_dt:
                    flash("End time must be after start time.", "danger")
                else:
                    # Avoid duplicate date entries
                    if not any(s["date"] == date_val for s in slots):
                        slots.append({
                            "date":       date_val,
                            "start_time": start_val,
                            "end_time":   end_val,
                        })
                        session[session_key] = slots
                    else:
                        flash("You already added a slot for that date.", "danger")

        elif action == "remove":
            idx = int(request.form.get("slot_index", -1))
            if 0 <= idx < len(slots):
                slots.pop(idx)
                session[session_key] = slots

        return redirect(url_for("employee_availability_enter",
                                employee_id=employee_id, period_id=period_id))

    # Mark calendar days that have slots
    slot_dates = {s["date"] for s in slots}
    for week in period["calendar_weeks"]:
        for day in week:
            day["has_slot"] = day["value"] in slot_dates

    # Format slots for display
    from datetime import datetime
    display_slots = []
    for s in slots:
        start_dt = datetime.strptime(f"{s['date']} {s['start_time']}", "%Y-%m-%d %H:%M")
        end_dt   = datetime.strptime(f"{s['date']} {s['end_time']}",   "%Y-%m-%d %H:%M")
        display_slots.append({
            "date_label":  start_dt.strftime("%a, %b %d"),
            "start_label": start_dt.strftime("%I:%M %p"),
            "end_label":   end_dt.strftime("%I:%M %p"),
        })

    return render_template(
        "employee_availability_enter.html",
        employee=employee,
        period=period,
        slots=display_slots,
        time_options=get_time_options(),
    )


@app.route("/employee/<int:employee_id>/availabilities/<int:period_id>/review", methods=["GET"])
def employee_availability_review(employee_id: int, period_id: int):
    from datetime import datetime
    employee = Employee.query.get_or_404(employee_id)
    sp       = SchedulingPeriod.query.get_or_404(period_id)
    period   = build_period_dict(sp, employee_id)

    session_key = f"avail_slots_{employee_id}_{period_id}"
    slots_raw   = session.get(session_key, [])

    if not slots_raw:
        flash("Please add at least one time slot before reviewing.", "danger")
        return redirect(url_for("employee_availability_enter",
                                employee_id=employee_id, period_id=period_id))

    # Build display slots with hours
    display_slots = []
    total_minutes = 0
    for s in slots_raw:
        start_dt = datetime.strptime(f"{s['date']} {s['start_time']}", "%Y-%m-%d %H:%M")
        end_dt   = datetime.strptime(f"{s['date']} {s['end_time']}",   "%Y-%m-%d %H:%M")
        mins     = int((end_dt - start_dt).total_seconds() / 60)
        total_minutes += mins
        display_slots.append({
            "date_label":  start_dt.strftime("%a, %B %d, %Y"),
            "start_label": start_dt.strftime("%H:%M"),
            "end_label":   end_dt.strftime("%H:%M"),
            "hours":       round(mins / 60, 1),
        })

    total_hours = round(total_minutes / 60, 1)
    avg_hours   = round(total_hours / len(display_slots), 1) if display_slots else 0

    summary = {
        "total_hours": total_hours,
        "days_count":  len(display_slots),
        "slot_count":  len(display_slots),
        "avg_hours":   avg_hours,
    }

    return render_template(
        "employee_availability_review.html",
        employee=employee,
        period=period,
        slots=display_slots,
        summary=summary,
    )


@app.route("/employee/<int:employee_id>/availabilities/<int:period_id>/submit", methods=["POST"])
def employee_availability_submit(employee_id: int, period_id: int):
    from datetime import datetime
    from src.availability_record import AvailabilityRecord

    employee    = Employee.query.get_or_404(employee_id)
    sp          = SchedulingPeriod.query.get_or_404(period_id)
    period      = build_period_dict(sp, employee_id)
    session_key = f"avail_slots_{employee_id}_{period_id}"
    slots_raw   = session.get(session_key, [])

    if not slots_raw:
        flash("No availability slots to submit.", "danger")
        return redirect(url_for("employee_availability_enter",
                                employee_id=employee_id, period_id=period_id))

    submission_ids = []
    try:
        # Remove any existing records for this period/employee before resubmitting
        AvailabilityRecord.query.filter_by(
            employeeID=employee_id, periodID=period_id
        ).delete()

        for s in slots_raw:
            start_dt = datetime.strptime(f"{s['date']} {s['start_time']}", "%Y-%m-%d %H:%M")
            end_dt   = datetime.strptime(f"{s['date']} {s['end_time']}",   "%Y-%m-%d %H:%M")
            record   = AvailabilityRecord(
                employeeID=employee_id,
                periodID=period_id,
                day=start_dt.strftime("%A"),
                start_time=start_dt,
                end_time=end_dt,
                status="pending",
            )
            db.session.add(record)
            db.session.flush()
            submission_ids.append(record.availabilityID)

        db.session.commit()

        # Clear session slots
        session.pop(session_key, None)

        submitted_at = datetime.now().strftime("%B %d, %Y at %I:%M %p")

        return render_template(
            "employee_availability_success.html",
            employee=employee,
            period=period,
            submitted_at=submitted_at,
            submission_ids=submission_ids,
        )

    except Exception as e:
        db.session.rollback()
        flash(f"Submission failed: {str(e)}", "danger")
        return redirect(url_for("employee_availability_review",
                                employee_id=employee_id, period_id=period_id))


# --- MANAGER: SCHEDULING PERIOD ROUTES ----------------------------------------------

@app.route("/manager/<int:manager_id>/periods", methods=["GET"])
def manager_periods(manager_id: int):
    if session.get('user_role') != 'manager' or session.get('user_id') != manager_id:
        return redirect(url_for('login'))
    manager = Manager.query.get_or_404(manager_id)
    periods = SchedulingPeriod.query.order_by(SchedulingPeriod.start_date.desc()).all()
    return render_template("manager_periods_list.html", manager=manager, periods=periods)


@app.route("/manager/<int:manager_id>/periods/create", methods=["GET", "POST"])
def manager_create_period(manager_id: int):
    from datetime import datetime
    if session.get('user_role') != 'manager' or session.get('user_id') != manager_id:
        return redirect(url_for('login'))
    manager = Manager.query.get_or_404(manager_id)

    if request.method == "POST":
        label      = request.form.get("label", "").strip()
        start_date = request.form.get("start_date", "").strip()
        end_date   = request.form.get("end_date", "").strip()
        due_date   = request.form.get("due_date", "").strip()
        status     = request.form.get("status", "upcoming").strip()

        try:
            sp = SchedulingPeriod(
                label      = label,
                start_date = datetime.strptime(start_date, "%Y-%m-%d").date(),
                end_date   = datetime.strptime(end_date,   "%Y-%m-%d").date(),
                due_date   = datetime.strptime(due_date,   "%Y-%m-%d").date(),
                status     = status,
                created_by = manager_id,
            )
            db.session.add(sp)
            db.session.commit()
            flash(f"Scheduling period '{label}' created successfully.", "success")
            return redirect(url_for("manager_periods", manager_id=manager_id))
        except Exception as e:
            db.session.rollback()
            flash(f"Error creating period: {str(e)}", "danger")

    return render_template("manager_create_period.html", manager=manager)


@app.route("/manager/<int:manager_id>/periods/<int:period_id>/close", methods=["POST"])
def manager_close_period(manager_id: int, period_id: int):
    if session.get('user_role') != 'manager' or session.get('user_id') != manager_id:
        return redirect(url_for('login'))
    sp = SchedulingPeriod.query.get_or_404(period_id)
    sp.close()
    flash(f"Period '{sp.label}' has been closed.", "success")
    return redirect(url_for("manager_periods", manager_id=manager_id))

# Redirections

@app.route("/demo/employee", methods=["GET"])
def demo_employee_redirect():
    employee = Employee.query.order_by(Employee.employeeID.asc()).first()
    if not employee:
        flash("No employees exist yet. Run seed_data.py (or create an employee) to view UC5.", "danger")
        return redirect(url_for("home"))
    return redirect(url_for("employee_jobs", employee_id=employee.employeeID))


@app.route("/demo/manager", methods=["GET"])
def demo_manager_redirect():
    manager = Manager.query.order_by(Manager.managerID.asc()).first()
    if not manager:
        flash("No managers exist yet. Run seed_data.py (or create a manager) to view UC7.", "danger")
        return redirect(url_for("home"))
    return redirect(url_for("manager_availability", manager_id=manager.managerID))


# --- UC1: AUTH ROUTES (Login / Signup / Logout / Vehicle Info / Edit profile) ---

from werkzeug.security import generate_password_hash

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':
        role_tab   = request.form.get('role_tab')
        email      = request.form.get('email', '').strip().lower()
        password   = request.form.get('password', '').strip()
        department = request.form.get('department', '')

        if role_tab == 'staff' and not email.endswith('@xpair.com'):
            flash("Staff access requires an @xpair.com email address.", "danger")
            return redirect(url_for('login'))

        if role_tab == 'customer':
            user = Customer.query.filter_by(email=email).first()
            if user and user.authenticate_user(password):
                session['user_id']   = user.customerID
                session['user_role'] = 'customer'
                session['user_name'] = user.first_name
                flash("Welcome back to Xpair Detailing!", "success")
                return redirect(url_for('home'))
            flash("Invalid email or password.", "danger")
            return redirect(url_for('login'))

        else:
            if department == 'management':
                user = Manager.query.filter_by(email=email).first()
                if user and user.authenticate_user(password):
                    session['user_id']   = user.managerID
                    session['user_role'] = 'manager'
                    session['user_name'] = user.first_name
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
        f_name     = request.form.get('first_name', '').strip()
        l_name     = request.form.get('last_name', '').strip()
        email      = request.form.get('email', '').strip().lower()
        phone      = request.form.get('phone', '').strip()
        password   = request.form.get('password', '').strip()
        confirm_pw = request.form.get('confirm_password', '').strip()
        department = request.form.get('department', '')

        if role_tab == 'staff' and not email.endswith('@xpair.com'):
            flash("Staff accounts must use a valid @xpair.com business email.", "danger")
            return redirect(url_for('signup'))

        if password != confirm_pw:
            flash("Passwords do not match.", "danger")
            return redirect(url_for('signup'))

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
            return redirect(url_for('signup'))

        hashed_pw = generate_password_hash(password)

        # Check against the shared person table — covers Customer, Employee, Manager
        if Person.query.filter_by(email=email).first():
            flash("An account with that email already exists.", "danger")
            return redirect(url_for('signup'))

        if role_tab == 'customer':
            new_user = Customer(
                first_name=f_name, last_name=l_name,
                email=email, phone=phone,
                password=hashed_pw, role='customer', address=''
            )
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
                new_user = Employee(
                    first_name=f_name, last_name=l_name,
                    email=email, phone=phone, password=hashed_pw,
                    role='employee', experience_level='junior',
                    position='Detailer', salary=18.50, working_hours=40.0
                )
                new_user.create_profile()
                flash("Account created! Welcome to Xpair Detailing.", "success")
                session['user_id']   = new_user.employeeID
                session['user_role'] = 'employee'
                session['user_name'] = new_user.first_name
                return redirect(url_for('employee_jobs', employee_id=new_user.employeeID))

            elif department == 'management':
                new_user = Manager(
                    first_name=f_name, last_name=l_name,
                    email=email, phone=phone,
                    password=hashed_pw, max_car_capacity=5
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
                    new_vehicle = customer.add_vehicle(
                        make=make, model=model, year=int(year),
                        plate=plate, size=size, type='Car'
                    )
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
        f_name = request.form.get('first_name', '').strip()
        l_name = request.form.get('last_name', '').strip()
        email  = request.form.get('email', '').strip().lower()
        phone  = request.form.get('phone', '').strip()

        user.update_first_name(f_name)
        user.update_last_name(l_name)
        user.update_email(email)
        user.update_phone(phone)
        session['user_name'] = f_name

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
                            make=make, model=model, year=int(year),
                            plate=plate, size=size, type='Car'
                        )
                        user.vehicle_id = new_vehicle.vehicleID
                        db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    flash(f"Vehicle update failed: {str(e)}", "danger")
                    return redirect(url_for('profile'))

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

        if role == 'employee':
            return redirect(url_for('employee_jobs', employee_id=user.employeeID))
        elif role == 'manager':
            return redirect(url_for('manager_availability', manager_id=user.managerID))
        else:
            return redirect(url_for('home'))

    vehicle = None
    if role == 'customer' and user.vehicle_id:
        vehicle = Vehicle.query.get(user.vehicle_id)

    return render_template('edit_profile.html', user=user, vehicle=vehicle, role=role)


if __name__ == "__main__":
    app.run(debug=True, port=5000)