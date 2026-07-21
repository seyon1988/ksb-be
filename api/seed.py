import sys
import os
sys.path.append(os.path.dirname(__file__))

from database import engine, Base, SessionLocal
from models import AdminUser, AdminDetails, GlobalSetting
from auth import get_password_hash

def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Seed default theme setting if not exists
        theme_setting = db.query(GlobalSetting).filter(GlobalSetting.key == "active_theme").first()
        if not theme_setting:
            db.add(GlobalSetting(key="active_theme", value="option-2"))
            db.commit()

        # Check if 'biranavan' user exists
        admin = db.query(AdminUser).filter(AdminUser.username == "biranavan").first()

        # If old 'admin' exists, update it
        old_admin = db.query(AdminUser).filter(AdminUser.username == "admin").first()

        target_admin = admin or old_admin

        if target_admin:
            target_admin.username = "biranavan"
            target_admin.hashed_password = get_password_hash("biranavan2110")
            target_admin.is_active = True

            if not target_admin.details:
                target_admin.details = AdminDetails(
                    admin_id=target_admin.id,
                    full_name="Mr. Selvanathan Biranavan",
                    email="biranavan@ksbconstruction.com",
                    phone="+94 777578710",
                    role="Managing Director & Admin"
                )
            db.commit()
            print("Updated admin user to 'biranavan' with password 'biranavan2110'.")
        else:
            new_admin = AdminUser(
                username="biranavan",
                hashed_password=get_password_hash("biranavan2110"),
                is_active=True
            )
            db.add(new_admin)
            db.flush()

            admin_details = AdminDetails(
                admin_id=new_admin.id,
                full_name="Mr. Selvanathan Biranavan",
                email="biranavan@ksbconstruction.com",
                phone="+94 777578710",
                role="Managing Director & Admin"
            )
            db.add(admin_details)
            db.commit()
            print("Created admin user 'biranavan' with password 'biranavan2110'.")
    except Exception as e:
        print("Error seeding admin:", e)
    finally:
        db.close()

if __name__ == "__main__":
    seed()
