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
# Database: SQLite file will be created in the root folder
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
        vehicle_size = request.form.get('vehicleSize').lower() # Sync with src validation
        date_str = request.form.get('date') # From Flatpickr
        time_str = request.form.get('time') # From our grid selection
        instructions = request.form.get('notes')
        
        # Capture Add-ons list and join into a comma-separated string
        addons_list = request.form.getlist('addons')
        
        # 3. Handle Time Logic (Converting strings to Python DateTime objects)
        try:
            # Combine Date and Time strings (e.g., "2026-03-30 9:00 AM")
            start_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %I:%M %p")
            
            # Fetch the service to calculate the correct end_time
            selected_service = Service.query.get(service_id)
            end_dt = start_dt + timedelta(minutes=selected_service.service_duration)
        except Exception as e:
            flash(f"Invalid Date or Time selection: {e}", "danger")
            return redirect(url_for('booking_page'))

        # 4. Integrate UC1: Handle Customer/Person record
        # --- HANDLE CUSTOMER (Use Case 1 Integration) ---
        customer = Customer.query.filter_by(email=email).first()
        
        if not customer:
            # Use the variables we got from request.form.get()
            customer = Customer(
                first_name=f_name,     # Now it uses the actual form input!
                last_name=l_name,      # Now it uses the actual form input!
                email=email, 
                phone=phone,
                password="guest_placeholder_123",
                role="customer",
                address="Guest Checkout"
            )
            db.session.add(customer)
            db.session.commit()

        # 5. Handle Vehicle record
        # Use the phone number or a timestamp to make the plate unique for each guest
        unique_plate = f"GUEST-{phone[-4:]}-{datetime.now().strftime('%S')}"

        new_vehicle = Vehicle(
            make="Guest", 
            model="Vehicle", 
            year=2026, 
            plate=unique_plate,   # This will now be unique every time!
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
        # Matches your exact 'src' attributes: booking_status, start_time, etc.
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
            
            # REDIRECT to the success page with the ID we just created
            return redirect(url_for('booking_success', booking_id=new_booking.bookingID))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Database Error: {str(e)}", "danger")
            return redirect(url_for('booking_page'))

# --- NEW ROUTES FOR MANAGE/RESCHEDULE/CANCEL ---

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
    # Use your class method!
    booking.cancel() 
    flash("Your booking has been successfully cancelled.", "info") # We'll turn this into a toast
    return redirect(url_for('home'))

@app.route('/reschedule/<int:booking_id>', methods=['GET', 'POST'])
def reschedule_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    
    if request.method == 'POST':
        # 1. Get the new data from the Reschedule Form
        new_date_str = request.form.get('date')
        new_time_str = request.form.get('time')
        
        try:
            # 2. Convert strings to Python DateTime objects
            new_start = datetime.strptime(f"{new_date_str} {new_time_str}", "%Y-%m-%d %I:%M %p")
            new_end = new_start + timedelta(minutes=booking.service.service_duration)
            
            # 3. Use YOUR Class Method from src/booking.py
            booking.reschedule(new_start, new_end)
            
            # 4. Trigger the Toast Notification (Attachment 5)
            flash(f"Your appointment has been rescheduled to {new_date_str} at {new_time_str}.", "success")
            
            # 5. Send them back to the Manage page to see the update
            return redirect(url_for('manage_booking', booking_id=booking.bookingID))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error rescheduling: {str(e)}", "danger")
            return redirect(url_for('reschedule_booking', booking_id=booking.bookingID))

    return render_template('reschedule.html', booking=booking)


if __name__ == "__main__":
    # Standard development server on port 5000
    app.run(debug=True, port=5000)