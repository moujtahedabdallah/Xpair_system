from app import app
from src.database import db
from sqlalchemy import text

# This will be used to reset the database whenever we want to populate the tables with different values.

def reset_database():
    with app.app_context():
        print("PREPARING RESET...")
        
        # Wipes the entire schema.
        try:
            db.session.execute(text("""
                DROP SCHEMA public CASCADE;
                CREATE SCHEMA public;
                GRANT ALL ON SCHEMA public TO public;
            """))
            db.session.commit()
            print("NEON SCHEMA WIPED CLEAN.")
        except Exception as e:
            db.session.rollback()
            print(f"Error during wipe: {e}")

        # Now recreate the tables based on your NEW, simplified Python models
        db.create_all()
        print("Database is now RESET.")

if __name__ == "__main__":
    reset_database()