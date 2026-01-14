"""
Disable character rating triggers
Python 코드에서 activities를 직접 관리하므로 트리거 비활성화
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import db


def disable_triggers():
    """캐릭터 rating 트리거 삭제 (Python 코드에서 직접 처리)"""

    print("Disabling character rating triggers...\n")

    triggers_to_drop = [
        'trg_character_rating_insert',
        'trg_character_rating_update',
        'trg_character_rating_delete'
    ]

    for trigger_name in triggers_to_drop:
        try:
            db.execute_update(f"DROP TRIGGER IF EXISTS {trigger_name}")
            print(f"✓ Dropped {trigger_name}")
        except Exception as e:
            print(f"✗ Failed to drop {trigger_name}: {e}")

    print("\n✓ Character rating triggers disabled")
    print("Activities are now managed directly by Python code (_sync_character_rating_to_activities)")


if __name__ == "__main__":
    try:
        print("=" * 60)
        print("Disabling Character Rating Triggers")
        print("=" * 60)

        disable_triggers()

        print("\n" + "=" * 60)
        print("✓ Trigger disable completed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
