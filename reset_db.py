from app import app
from src.database import db

# This will be used to reset the database whenever we want to populate the tables with different values.

def reset_database():
    with app.app_context():
        print("PREPARING RESET FOR SQLITE...")
        
        try:
            # This single line safely wipes every table in your SQLite database
            db.drop_all()
            print("SQLITE TABLES WIPED CLEAN.")
        except Exception as e:
            print(f"Error during wipe: {e}")

        # Recreate the empty tables based on your models
        db.create_all()
        print("Database is now RESET and ready for fresh data.")

if __name__ == "__main__":
    reset_database()