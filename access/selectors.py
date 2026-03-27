from django.utils import timezone
from datetime import timedelta

from access.models import EntryLog


def is_in_cooldown(member_id: int, branch_id: int, cooldown_seconds: int, at_time=None) -> bool:
    at_time = at_time or timezone.now()
    since = at_time - timedelta(seconds=cooldown_seconds)
    
    if not cooldown_seconds or cooldown_seconds <= 0:
        return False
    
    return EntryLog.objects.filter(
        member_id=member_id,
        branch_id=branch_id,
        allow=True,
        created_at__gte=since,
    ).exists()