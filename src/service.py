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

    # Methods
    def calculate_quote_price(self, vehicle_size, add_ons):
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
            'interior_cleaning': 30.00,
            'engine_cleaning': 50.00,
            'ceramic_coating': 150.00,
            'paint_correction': 200.00
        }

        # Base price adjusted by vehicle size
        multiplier = size_multipliers.get(vehicle_size, 1.0)
        total = self.base_price * multiplier

        # Add the price of each selected add-on
        for add_on in add_ons:
            total += add_on_prices.get(add_on, 0)

        return round(total, 2)