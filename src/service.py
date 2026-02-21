from .database import db

class Service(db.Model):
    __tablename__ = 'service'

    # Variables
    serviceID = db.Column(db.Integer, primary_key=True)
    service_name = db.Column(db.String(100), nullable=False)
    service_duration = db.Column(db.Integer, nullable=False)  # in minutes
    description = db.Column(db.String(500))
    base_price = db.Column(db.Float, nullable=False)
    available_add_ons = db.Column(db.JSON, default=list)
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    #Service data table
    SERVICE_DATA = {
    "Basic Package": {"price": 100.0, "duration": 60},
    "Xpair Supreme Package": {"price": 150.0, "duration": 180},
    "Ultimate Xpair Exterior Package": {"price": 200.0, "duration": 240},
    "Complete Engine Cleaning": {"price": 60.0, "duration": 45},
    "Black Surface Restoration (Tires)": {"price": 40.0, "duration": 20},
    "Black Surface Restoration (Plastics)": {"price": 45.0, "duration": 30},
    "Complete Paint Decontamination": {"price": 90.0, "duration": 90},
    "One-Step Polishing": {"price": 250.0, "duration": 300},
    "Two-Step Correction": {"price": 450.0, "duration": 480},
    "Xpair Nano Ceramic Coating": {"price": 800.0, "duration": 600},
    "Xpair Ceramic Spray Coating": {"price": 120.0, "duration": 120}
}

    # Methods

    def apply_preset(self, name):
        # Fills in details based on the service name
        data = self.SERVICE_DATA.get(name)
        
        if data:
            self.service_name = name
            self.base_price = data['price']
            self.service_duration = data['duration']
            self.description = f" {name} service."

            self.available_add_ons = [
                "UV Protection for Plastics",
                "Detailed Seat Cleaning",
                "Deep Carpet and Floor Cleaning",
                "Water-Repellent Product for Carpets",
                "Leather Seat Conditioner",
                "Xpair Detailing Air Freshener",
                "Odor Neutralizer",
                "Black Surface Restoration (Tires)",
                "Black Surface Restoration (Plastics)"
            ]


    def calculate_quote_price(self, vehicle_size, selected_add_ons=None):
        # Calculates total price based on vehicle size and selected add-ons
        # Example pricing rules (will be changed to align with actual business logic):
        # Size multipliers
        size_multipliers = {
            'small': 1.0,
            'medium': 1.25,
            'large': 1.5
        }

        # Add-on prices
        add_on_prices = {
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
        # Base price adjusted by vehicle size
        multiplier = size_multipliers.get(vehicle_size.lower(), 1.0)
        total = self.base_price * multiplier

        # Add the price of each selected add-on
        if selected_add_ons:
            for extra in selected_add_ons:
                price = add_on_prices.get(extra, 0.0)
                total += price

        return round(total, 2)