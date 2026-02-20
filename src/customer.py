from .database import db
from .person import Person
from .booking import Booking
from .service import Service
from .vehicle import Vehicle


class Customer(Person):
    __tablename__ = 'customer'

    # Variables
    customerID = db.Column(db.Integer, db.ForeignKey('person.id'), primary_key=True)
    booking_history = db.Column(db.Text)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.vehicleID'))


    # Methods
    def enter_preferences(self, vehicleID):
        # Sets the customer's preferred vehicle
        vehicle = Vehicle.query.get(vehicleID)
        if not vehicle:
            raise ValueError(f"Vehicle with ID {vehicleID} not found.")
        self.vehicle_id = vehicleID
        db.session.commit()

    def view_catalog(self):
        # Returns all available services from the catalog
        return Service.query.all()

    def select_service_type(self, serviceID):
        # Selects and returns a service type from the catalog
        service = Service.query.get(serviceID)
        if not service:
            raise ValueError(f"Service with ID {serviceID} not found.")
        return service

    def select_vehicle_size(self, size):
        # Validates the requested vehicle size and updates the customer's vehicle record
        valid_sizes = ['small', 'medium', 'large']
        if size not in valid_sizes:
            raise ValueError(f"Invalid size '{size}'. Must be one of: {valid_sizes}")
        if self.vehicle_id:
            vehicle = Vehicle.query.get(self.vehicle_id)
            if vehicle:
                vehicle.update_size(size)
        return size

    def request_and_review_quote(self, serviceID, availableAddOns):
        # Calculates and returns a price quote for the selected service and add-ons
        service = Service.query.get(serviceID)
        if not service:
            raise ValueError(f"Service with ID {serviceID} not found.")

        vehicle_size = 'medium'  # default fallback
        if self.vehicle_id:
            vehicle = Vehicle.query.get(self.vehicle_id)
            if vehicle and vehicle.size:
                vehicle_size = vehicle.size

        total_price = service.calculate_quote_price(vehicle_size, availableAddOns)
        return {
            'service_name': service.service_name,
            'vehicle_size': vehicle_size,
            'add_ons': availableAddOns,
            'total_price': total_price,
        }

    def book_service(self, serviceID, vehicleID, startTime):
        # Creates and saves a new booking for the customer
        service = Service.query.get(serviceID)
        if not service:
            raise ValueError(f"Service with ID {serviceID} not found.")

        from datetime import timedelta
        end_time = startTime + timedelta(minutes=service.service_duration)

        booking = Booking(
            periodID=0,  # assign correct periodID externally if needed
            date=startTime.date(),
            start_time=startTime,
            end_time=end_time,
            is_available=True,
            is_blocked=False,
            booking_status='pending',
        )
        db.session.add(booking)
        db.session.commit()

        # Append booking to history
        booking_id_str = str(booking.bookingID)
        self.booking_history = (
            (self.booking_history + ',' + booking_id_str)
            if self.booking_history
            else booking_id_str
        )
        self.vehicle_id = vehicleID
        db.session.commit()

        return booking

    def manage_booking(self, bookingID):
        # Returns the booking details for a given booking ID belonging to this customer
        booking = Booking.query.get(bookingID)
        if not booking:
            raise ValueError(f"Booking with ID {bookingID} not found.")
        return booking

    def cancel_booking(self, bookingID):
        # Cancels an existing booking for the customer
        booking = Booking.query.get(bookingID)
        if not booking:
            raise ValueError(f"Booking with ID {bookingID} not found.")
        if booking.booking_status == 'cancelled':
            raise ValueError(f"Booking {bookingID} is already cancelled.")
        booking.cancel()
