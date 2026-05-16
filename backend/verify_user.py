
from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import verify_password

db = SessionLocal()
try:
    user = db.query(User).filter(User.email == "admin@example.com").first()
    if user:
        print(f"User found: {user.email}")
        print(f"Role: {user.role}")
        is_valid = verify_password("admin123", user.password_hash)
        print(f"Password 'admin123' is valid: {is_valid}")
    else:
        print("User NOT found")
finally:
    db.close()
