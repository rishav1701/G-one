import uuid

from argon2 import PasswordHasher
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.core.demo_credentials import DEMO_ACCOUNT_PASSWORDS
from app.models.base import AppUser, AuditLog, Role, Session as UserSession, UserWard, Ward


hasher = PasswordHasher()


def seed_users(
    db: Session,
    *,
    admin_username: str,
    admin_password: str,
    clinician_username: str,
    clinician_password: str,
    sync_demo_passwords: bool = False,
) -> list[str]:
    """Create accounts and optionally synchronize public development-demo passwords."""
    messages: list[str] = []

    admin = db.scalar(select(AppUser).where(AppUser.username == admin_username))
    if admin is None:
        admin = AppUser(
            username=admin_username,
            password_hash=hasher.hash(admin_password),
            role=Role.ADMIN,
            active=True,
        )
        db.add(admin)
        db.flush()
        messages.append(f"Created ADMIN demo account {admin_username}.")
    elif admin.role is not Role.ADMIN:
        messages.append(
            f"{admin_username} exists with a different role; no changes were made. "
            "Choose another SEED_ADMIN_USERNAME."
        )
        db.commit()
        return messages
    else:
        if sync_demo_passwords:
            db.query(UserSession).filter_by(user_id=admin.id).delete(synchronize_session=False)
            admin.password_hash = hasher.hash(admin_password)
            admin.failed_logins = 0
            admin.locked_until = None
            db.add(AuditLog(actor_id=None, action="seed.demo_password_sync", object_type="app_user", object_id=admin.id, request_id=str(uuid.uuid4())))
            messages.append(f"Local demo credentials synchronized for ADMIN {admin_username}.")
        else:
            messages.append(f"ADMIN {admin_username} already exists; credentials were not changed.")
    db.query(UserWard).filter_by(user_id=admin.id).delete(synchronize_session=False)

    simulated_wards = list(
        db.scalars(
            select(Ward).where(Ward.name.like("Simulation Ward %")).order_by(Ward.name)
        ).all()
    )
    clinician = db.scalar(select(AppUser).where(AppUser.username == clinician_username))
    if clinician is None:
        clinician = AppUser(
            username=clinician_username,
            password_hash=hasher.hash(clinician_password),
            role=Role.SENIOR_CLINICIAN,
            active=True,
        )
        db.add(clinician)
        db.flush()
        messages.append(f"Created SENIOR_CLINICIAN demo account {clinician_username}.")
    elif clinician.role is not Role.SENIOR_CLINICIAN:
        messages.append(
            f"{clinician_username} exists with a different role; no changes were made. "
            "Choose another SEED_CLINICIAN_USERNAME."
        )
        db.commit()
        return messages
    else:
        if sync_demo_passwords:
            db.query(UserSession).filter_by(user_id=clinician.id).delete(synchronize_session=False)
            clinician.password_hash = hasher.hash(clinician_password)
            clinician.failed_logins = 0
            clinician.locked_until = None
            db.add(AuditLog(actor_id=None, action="seed.demo_password_sync", object_type="app_user", object_id=clinician.id, request_id=str(uuid.uuid4())))
            messages.append(f"Local demo credentials synchronized for SENIOR_CLINICIAN {clinician_username}.")
        else:
            messages.append(
                f"SENIOR_CLINICIAN {clinician_username} already exists; credentials were not changed."
            )

    if not simulated_wards:
        messages.append(
            "No simulator wards exist; the clinician account will receive ward access after simulator seeding."
        )
        db.commit()
        return messages

    ward_ids = {ward.id for ward in simulated_wards}
    assigned_ids = set(
        db.scalars(select(UserWard.ward_id).where(UserWard.user_id == clinician.id)).all()
    )
    if assigned_ids != ward_ids:
        db.query(UserWard).filter_by(user_id=clinician.id).delete(synchronize_session=False)
        db.add_all(UserWard(user_id=clinician.id, ward_id=ward_id) for ward_id in sorted(ward_ids))

    db.commit()
    return messages


def main():
    admin_username = "phaseadmin"
    clinician_username = "phaseclinician"
    admin_password = DEMO_ACCOUNT_PASSWORDS["admin"]
    clinician_password = DEMO_ACCOUNT_PASSWORDS["clinician"]
    sync_demo_passwords = True

    db = SessionLocal()
    try:
        for message in seed_users(
            db,
            admin_username=admin_username,
            admin_password=admin_password,
            clinician_username=clinician_username,
            clinician_password=clinician_password,
            sync_demo_passwords=sync_demo_passwords,
        ):
            print(message)
    finally:
        db.close()


if __name__ == "__main__":
    main()
