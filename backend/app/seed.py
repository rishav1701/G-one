import os,secrets
from argon2 import PasswordHasher
from app.core.db import SessionLocal
from app.models.base import AppUser,Role,Ward,UserWard

def main():
    username=os.environ.get("SEED_ADMIN_USERNAME","admin")
    password=os.environ.get("SEED_ADMIN_PASSWORD") or secrets.token_urlsafe(18)
    db=SessionLocal()
    try:
        if db.query(AppUser).filter_by(username=username).first(): raise SystemExit("Seed user already exists; refusing to reset credentials")
        ward=Ward(name="Ward 1"); db.add(ward); db.flush()
        user=AppUser(username=username,password_hash=PasswordHasher().hash(password),role=Role.ADMIN,active=True)
        db.add(user); db.flush(); db.add(UserWard(user_id=user.id,ward_id=ward.id)); db.commit()
        print(f"Generated one-time password for {username}: {password}")
    finally: db.close()
if __name__=="__main__": main()
