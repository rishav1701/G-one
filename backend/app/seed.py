import os
import secrets

from argon2 import PasswordHasher
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.models.base import AppUser, Role, UserWard, Ward


hasher = PasswordHasher()


def seed_users(
    db: Session,
    *,
    admin_username: str,
    admin_password: str,
    clinician_username: str,
    clinician_password: str,
) -> list[str]:
    """Create separate demo accounts without changing existing credentials."""
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
        messages.append(f"Generated one-time password for ADMIN {admin_username}: {admin_password}")
    elif admin.role is not Role.ADMIN:
        messages.append(
            f"{admin_username} exists with a different role; no changes were made. "
            "Choose another SEED_ADMIN_USERNAME."
        )
        db.commit()
        return messages
    else:
        messages.append(f"ADMIN {admin_username} already exists; credentials were not changed.")
    db.query(UserWard).filter_by(user_id=admin.id).delete(synchronize_session=False)

    simulated_wards = list(
        db.scalars(
            select(Ward).where(Ward.name.like("Simulation Ward %")).order_by(Ward.name)
        ).all()
    )
    if not simulated_wards:
        messages.append(
            "No simulator wards exist. Run the simulator reset command, then seed users again."
        )
        db.commit()
        return messages

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
        messages.append(
            "Generated one-time password for SENIOR_CLINICIAN "
            f"{clinician_username}: {clinician_password}"
        )
    elif clinician.role is not Role.SENIOR_CLINICIAN:
        messages.append(
            f"{clinician_username} exists with a different role; no changes were made. "
            "Choose another SEED_CLINICIAN_USERNAME."
        )
        db.commit()
        return messages
    else:
        messages.append(
            f"SENIOR_CLINICIAN {clinician_username} already exists; credentials were not changed."
        )

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
    admin_username = os.environ.get("SEED_ADMIN_USERNAME", "phaseadmin")
    admin_password = os.environ.get("SEED_ADMIN_PASSWORD") or secrets.token_urlsafe(18)
    clinician_username = os.environ.get("SEED_CLINICIAN_USERNAME", "phaseclinician")
    clinician_password = os.environ.get("SEED_CLINICIAN_PASSWORD") or secrets.token_urlsafe(18)

    db = SessionLocal()
    try:
        for message in seed_users(
            db,
            admin_username=admin_username,
            admin_password=admin_password,
            clinician_username=clinician_username,
            clinician_password=clinician_password,
        ):
            print(message)
    finally:
        db.close()


if __name__ == "__main__":
    main()
