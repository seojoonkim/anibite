"""
Verify all existing users
기존 사용자들을 모두 인증 완료 상태로 변경
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import db


def verify_existing_users():
    """기존 사용자들을 모두 인증 완료 처리"""

    print("Verifying existing users...")

    # Check current status
    rows = db.execute_query(
        "SELECT COUNT(*) as total, SUM(CASE WHEN is_verified = 1 THEN 1 ELSE 0 END) as verified FROM users"
    )
    total = rows[0][0] if rows else 0
    verified = rows[0][1] if rows else 0
    unverified = total - verified

    print(f"\nCurrent status:")
    print(f"  Total users: {total}")
    print(f"  Verified: {verified}")
    print(f"  Unverified: {unverified}")

    if unverified == 0:
        print("\n✓ All users are already verified!")
        return

    # Update all users to verified
    updated = db.execute_update(
        """
        UPDATE users
        SET is_verified = 1,
            verification_token = NULL,
            verification_token_expires = NULL,
            updated_at = CURRENT_TIMESTAMP
        WHERE is_verified = 0 OR is_verified IS NULL
        """
    )

    print(f"\n✓ Updated {updated} users to verified status")

    # Show updated status
    rows = db.execute_query(
        "SELECT COUNT(*) as total, SUM(CASE WHEN is_verified = 1 THEN 1 ELSE 0 END) as verified FROM users"
    )
    total = rows[0][0] if rows else 0
    verified = rows[0][1] if rows else 0

    print(f"\nFinal status:")
    print(f"  Total users: {total}")
    print(f"  Verified: {verified}")


if __name__ == "__main__":
    verify_existing_users()
