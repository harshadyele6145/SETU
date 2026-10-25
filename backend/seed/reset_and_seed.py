import sys
import os

sys.path.insert(0, os.path.abspath("."))

from backend.app.core.config import settings
from backend.app.core.database import engine, Base, SessionLocal
from backend.seed.seed_data import seed_database
from backend.app.services.audit_service import audit_service


def reset_and_seed():
    print("=" * 65)
    print("SETU LOCAL DEMO ENVIRONMENT RESET & SYNTHETIC DATA SEEDING")
    print("=" * 65)

    if not settings.DEMO_MODE:
        print("ERROR: Safety Guard Tripped! DEMO_MODE is not True. Refusing destructive reset.")
        sys.exit(1)

    print("WARNING: Resetting all local demonstration tables in database...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("All tables dropped and re-created successfully.")

    print("\nRunning synthetic database seeding...")
    db = SessionLocal()
    try:
        seed_database(db, generate_alerts=True)
        is_valid, count, broken_seq, msg = audit_service.verify_chain(db)
        print(f"\nCryptographic Audit Trail Verification: {msg} (Verified {count} events)")
    finally:
        db.close()

    print("\nReset & Seed complete. Demo environment is ready for evaluation!")


if __name__ == "__main__":
    reset_and_seed()

