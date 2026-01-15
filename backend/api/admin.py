"""
Admin API - Temporary endpoints for database migrations
임시 관리자 API
"""
from fastapi import APIRouter, HTTPException
from database import db

router = APIRouter()


@router.post("/verify-all-users")
def verify_all_users_endpoint():
    """
    Verify all existing users (temporary migration endpoint)
    기존 사용자 모두 인증 완료 처리 (임시 마이그레이션 엔드포인트)
    """
    try:
        # Check current status
        rows = db.execute_query(
            "SELECT COUNT(*) as total, SUM(CASE WHEN is_verified = 1 THEN 1 ELSE 0 END) as verified FROM users"
        )
        total = rows[0][0] if rows else 0
        verified_before = rows[0][1] if rows else 0
        unverified_before = total - verified_before

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

        # Check updated status
        rows = db.execute_query(
            "SELECT COUNT(*) as total, SUM(CASE WHEN is_verified = 1 THEN 1 ELSE 0 END) as verified FROM users"
        )
        verified_after = rows[0][1] if rows else 0

        return {
            "message": "All users verified successfully",
            "total_users": total,
            "verified_before": verified_before,
            "unverified_before": unverified_before,
            "verified_after": verified_after,
            "updated": updated
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to verify users: {str(e)}")


@router.get("/users-status")
def get_users_status():
    """
    Get users verification status
    사용자 인증 상태 확인
    """
    try:
        rows = db.execute_query(
            """
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN is_verified = 1 THEN 1 ELSE 0 END) as verified,
                SUM(CASE WHEN is_verified = 0 OR is_verified IS NULL THEN 1 ELSE 0 END) as unverified
            FROM users
            """
        )

        total = rows[0][0] if rows else 0
        verified = rows[0][1] if rows else 0
        unverified = rows[0][2] if rows else 0

        # Get sample unverified users
        unverified_users = db.execute_query(
            "SELECT id, username, email, is_verified FROM users WHERE is_verified = 0 OR is_verified IS NULL LIMIT 5"
        )

        unverified_list = [
            {
                "id": row[0],
                "username": row[1],
                "email": row[2],
                "is_verified": row[3]
            }
            for row in unverified_users
        ]

        return {
            "total_users": total,
            "verified": verified,
            "unverified": unverified,
            "unverified_sample": unverified_list
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")
