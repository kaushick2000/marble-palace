"""Create the first admin user.

Usage:
    python seed_admin.py --username admin --password "strong-password"

Falls back to ADMIN_USERNAME / ADMIN_PASSWORD env vars if flags are omitted.
"""
import argparse
import asyncio
import os

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.models.admin_user import AdminUser


async def seed_admin(username: str, password: str) -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(AdminUser).where(AdminUser.username == username))
        if result.scalar_one_or_none() is not None:
            print(f"Admin user '{username}' already exists. Skipping.")
            return

        admin = AdminUser(username=username, hashed_password=hash_password(password))
        db.add(admin)
        await db.commit()
        print(f"Created admin user '{username}'.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--username", default=os.environ.get("ADMIN_USERNAME"))
    parser.add_argument("--password", default=os.environ.get("ADMIN_PASSWORD"))
    args = parser.parse_args()

    if not args.username or not args.password:
        parser.error(
            "username and password are required (via --username/--password "
            "or ADMIN_USERNAME/ADMIN_PASSWORD env vars)"
        )

    asyncio.run(seed_admin(args.username, args.password))


if __name__ == "__main__":
    main()
