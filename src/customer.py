from .database import db
from .person import Person

class Customer(Person):
    # Inherits from person
    __tablename__ = 'customer'

    # Variables
    customerID = db.Column(db.Integer, db.ForeignKey('person.id'), primary_key=True)
    booking_history = db.Column(db.Text)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.vehicleID'), nullable=True)  # Tracks the customer's most recently used vehicle

    # Polymetric identity which essentially identifies this class as a part of the Person class
    __mapper_args__ = {
        'polymorphic_identity': 'customer',
    }

    # Methods
    def add_vehicle(self, make, model, year, plate, size = "medium", type = "car"):
        from .vehicle import Vehicle # solves the problem of circular imports by importing here instead of at the top of the file
        # Lets customer add a car to their profile
        added_car = Vehicle(
            make = make,
            model = model,
            year = year,
            plate = plate,
            size = size,
            type = type,
            customerID=self.customerID  # Links the car to the owner
        )
        db.session.add(added_car)
        db.session.commit()
        return added_car
    


    def view_catalog(self):
        from .service import Service # solves the problem of circular imports by importing here instead of at the top of the file
        # Returns all available services from the catalog
        return Service.query.all()

    def select_service_type(self, serviceID):
        from .service import Service # solves the problem of circular imports by importing here instead of at the top of the file
        # Selects and returns a service type from the catalog
        service = db.session.get(Service, serviceID)
        if not service:
            raise ValueError(f"Service with ID {serviceID} not found.")
        return service

    def select_vehicle_size(self, serviceID, size):
        from .vehicle import Vehicle # solves the problem of circular imports by importing here instead of at the top of the file
        # Validates the requested vehicle size and updates the customer's vehicle record
        valid_sizes = ['small', 'medium', 'large']
        if size not in valid_sizes:
            raise ValueError(f"Invalid size '{size}'. Must be one of: {valid_sizes}")
        if self.vehicle_id:
            vehicle = db.session.get(Vehicle, self.vehicle_id)
            if vehicle:
                vehicle.update_size(size)
        return size

    def request_and_review_quote(self, serviceID, selected_add_ons):
        from .service import Service # solves the problem of circular imports by importing here instead of at the top of the file
        from .vehicle import Vehicle # solves the problem of circular imports by importing here instead of at the top of the file
        # Calculates and returns a price quote for the selected service and add-ons
        service = db.session.get(Service, serviceID)
        if not service:
            raise ValueError(f"Service with ID {serviceID} not found.")

        # Default to medium, but changes it if the customer has a saved vehicle
        vehicle_size = 'medium'  # default fallback
        if self.vehicle_id:
            vehicle = db.session.get(Vehicle, self.vehicle_id)
            if vehicle and vehicle.size:
                vehicle_size = vehicle.size

        # Uses the service class' quote price method and returns details for quote 
        total_price = service.calculate_quote_price(vehicle_size, selected_add_ons)
        return {
            'service_name': service.service_name,
            'vehicle_size': vehicle_size,
            'add_ons': selected_add_ons,
            'total_price': total_price,
        }

    def book_service(self, serviceID, vehicleID, startTime):
        from .booking import Booking # solves the problem of circular imports by importing here instead of at the top of the file
        # Creates and saves a new booking for the customer
        service = db.session.get(Service, serviceID)
        if not service:
            raise ValueError(f"Service with ID {serviceID} not found.")
        

        # Check if a booking already exists for this customer at this time
        existing = Booking.query.filter_by(customerID=self.customerID, start_time=startTime).first()
        if existing:
            raise ValueError("You already have a booking at this time.")
        
        
        # Calculates the end time by adding the service duration to the requested start time
        from datetime import timedelta
        end_time = startTime + timedelta(minutes=service.service_duration)

        # Initialized the booking object
        booking = Booking(
            customerID=self.customerID,  
            serviceID=serviceID,        
            vehicleID=vehicleID,         
            date=startTime.date(),
            start_time=startTime,
            end_time=end_time,
            booking_status='pending'
        )
        db.session.add(booking)
        db.session.flush() # Flush pushes the object to the database to generate an ID 

        # Add booking to history
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
        from .booking import Booking # solves the problem of circular imports by importing here instead of at the top of the file
        # Returns the booking details for a given booking ID belonging to this customer
        booking = db.session.get(Booking, bookingID)
        if not booking:
            raise ValueError(f"Booking with ID {bookingID} not found.")
        return booking

    def cancel_booking(self, bookingID) -> bool:
        from .booking import Booking # solves the problem of circular imports by importing here instead of at the top of the file
        # Cancels an existing booking for the customer
        booking = db.session.get(Booking, bookingID)
        if not booking:
            raise ValueError(f"Booking with ID {bookingID} not found.")
        if booking.booking_status == 'cancelled':
            raise ValueError(f"Booking {bookingID} is already cancelled.")
        booking.cancel()
        return True