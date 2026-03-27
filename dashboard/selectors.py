from datetime import timedelta
from django.utils import timezone
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from users.models import Member
from access.models import EntryLog
from subscriptions.models import MemberSubscription
from branches.models import Branch
from django.db.models import OuterRef,Subquery

def active_members_count(gym_id: int) -> int:
    return Member.objects.filter(gym_id=gym_id, is_active=True).count()

def current_inside_count(gym_id: int) -> int:
    return Member.objects.filter(gym_id=gym_id, is_active=True, is_inside=True).count()

def today_entries_count(gym_id: int) -> int:
    now = timezone.now()
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return EntryLog.objects.filter(gym_id=gym_id, allow=True, event = EntryLog.EVENT_IN, created_at__gte=start).count()

def expiring_soon_count(gym_id: int, days: int = 7) -> int:
    now = timezone.now()
    until = now + timedelta(days=days)

    # Members with any subscription that ends within window
    # (simple v1: count distinct members)
    return (
        MemberSubscription.objects.filter(
            member__gym_id=gym_id,
            end_at__gt=now,
            end_at__lte=until,
        )
        .values("member_id")
        .distinct()
        .count()
    )
    


# ------------------- OWNER ---------------------------

def branch_income_chart_data(gym_id: int):
    rows = branch_analytics_rows(gym_id)
    labels = [r["branch_name"] for r in rows]
    values = [r["income_month"] for r in rows]
    return labels, values

def branch_active_members_chart_data(gym_id: int):
    rows = branch_analytics_rows(gym_id)
    labels = [r["branch_name"] for r in rows]
    values = [r["active_members"] for r in rows]
    return labels, values

def _month_range(months: int):
    now = timezone.now()
    start = (now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
             - timedelta(days=32 * (months - 2)))
    # normalize to first day of that month
    start = start.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return now, start

def income_by_month(gym_id: int, months: int, branch_id: int | None = None):
    now, start = _month_range(months)
    
    qs = MemberSubscription.objects.filter(
        member__gym_id=gym_id,
        created_at__gte=start,
        created_at__lte=now,
    )
    if branch_id:
        qs = qs.filter(member__branch_id=branch_id)
    
    
    rows = (
        qs
        .annotate(m=TruncMonth("created_at"))
        .values("m")
        .annotate(total=Sum("price_snapshot"))
        .order_by("m")
    )

    out = {}
    for r in rows:
        out[r["m"].date().isoformat()] = int(r["total"] or 0)
    
    labels = []
    values = []
    cur = start
    for _ in range(months):
        key = cur.date().isoformat()
        labels.append(cur.strftime("%b %Y"))
        values.append(out.get(key, 0))
        # jump to next month safely
        cur = (cur + timedelta(days=32)).replace(day=1)
    return labels, values

def members_new_by_month(gym_id: int, months: int, branch_id: int | None = None):
    now, start = _month_range(months)
    
    qs = (Member.objects
        .filter(gym_id=gym_id, created_at__gte=start, created_at__lte=now))
    
    if branch_id:
        qs = qs.filter(branch_id=branch_id)
    
    row = (
        qs
        .annotate(m=TruncMonth("created_at"))
        .values("m")
        .annotate(c=Count("id"))
        .order_by("m")
    )
    out = {r["m"].date().isoformat(): int(r["c"]) for r in row}
    labels, values = [], []
    cur = start
    for _ in range(months):
        key = cur.date().isoformat()
        labels.append(cur.strftime("%b %Y"))
        values.append(out.get(key, 0))
        cur = (cur + timedelta(days=32)).replace(day=1)
    return labels, values

def members_left_by_month(gym_id: int, months: int, branch_id: int | None = None):
    """
    v1 definition (simple + stable):
    left = members that were set is_active=False within month (requires updated_at).
    If you don't have updated_at, replace with an alternative later.
    """
    now, start = _month_range(months)

    qs = (Member.objects
        .filter(gym_id=gym_id, is_active=False, updated_at__gte=start, updated_at__lte=now))
    
    if branch_id:
        qs = qs.filter(branch_id=branch_id)
        
    row = (
        qs
        .annotate(m=TruncMonth("updated_at"))
        .values("m")
        .annotate(c=Count("id"))
        .order_by("m")
    )
    out = {r["m"].date().isoformat(): int(r["c"]) for r in row}
    labels, values = [], []
    cur = start
    for _ in range(months):
        key = cur.isoformat()
        labels.append(cur.strftime("%b %Y"))
        values.append(out.get(key, 0))
        cur = (cur + timedelta(days=32)).replace(day=1)
    return labels, values

def active_members_now(gym_id: int, branch_id: int | None = None):
    today = timezone.localdate()

    latest_sub = (
        MemberSubscription.objects
        .filter(member_id=OuterRef("pk"))
        .order_by("-start_at", "-id")
    )

    qs = (
        Member.objects
        .filter(gym_id=gym_id, is_active=True)
        .annotate(
            latest_end_at=Subquery(latest_sub.values("end_at")[:1]),
        )
        .filter(latest_end_at__gte=today)
    )

    if branch_id:
        qs = qs.filter(branch_id=branch_id)

    return qs.count()

def inside_now(gym_id: int, branch_id: int | None = None):
    if branch_id:
        return Member.objects.filter(gym_id=gym_id,branch_id = branch_id , is_inside=True).count()
    return Member.objects.filter(gym_id=gym_id, is_inside=True).count()

def expiring_counts(gym_id: int, branch_id: int | None = None):
    now = timezone.now().date()
    in_7 = now + timedelta(days=7)

    latest_sub = (
        MemberSubscription.objects
        .filter(member_id=OuterRef("pk"))
        .order_by("-start_at", "-id")
    )
    
    qs = (MemberSubscription.objects
        .filter(member__gym_id=gym_id, end_at__isnull=False))
    
    if branch_id:
        qs = qs.filter(member__branch_id=branch_id)
    
    subs = (
        qs.annotate(latest_end_at=Subquery(latest_sub.values("end_at")[:1]))
    )

    exp_today = subs.filter(latest_end_at = now).count()
    exp_7 = subs.filter(latest_end_at__lte=in_7, latest_end_at__gte=now).count()
    return exp_today, exp_7

def income_month(gym_id: int, offset_months: int = 0, branch_id: int | None = None):
    """
    offset_months=0 => current month
    offset_months=1 => previous month
    """
    now = timezone.now()
    # first day current month
    first = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    # start/end for target month
    
    last_month,last_year = 0,0
    if first.month == 1:
        last_month,last_year = 12,first.year - 1
    else:
        last_month,last_year = first.month - 1,first.year
    
    if not offset_months:
        start = first
    else:
        start = first.replace(year=last_year,month=last_month)
    
    end = (start + timedelta(days=32)).replace(day=1)
    
    qs = (MemberSubscription.objects
        .filter(member__gym_id=gym_id, created_at__gte=start, created_at__lt=end))

    if branch_id:
        qs = qs.filter(member__branch_id=branch_id)
    

    total = (
        qs.aggregate(s=Sum("price_snapshot"))
    )["s"] or 0
    # print("income month",total)
    return int(total)   

def branch_analytics_rows(gym_id: int):
    now = timezone.now()
    today = timezone.localdate()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    in_7 = now + timedelta(days=7)

    branches = list(Branch.objects.filter(gym_id=gym_id).order_by("id").values("id", "name"))
    if not branches:
        return []

    branch_ids = [b["id"] for b in branches]

# active/inside (still ok)
    latest_sub = (
        MemberSubscription.objects
        .filter(member_id=OuterRef("pk"))
        .order_by("-start_at", "-id")
    )

    qs = (
        Member.objects
        .filter(gym_id=gym_id, is_active=True)
        .annotate(
            latest_end_at=Subquery(latest_sub.values("end_at")[:1]),
        )
        .filter(latest_end_at__gte=today)
    )
    
    active_map = dict(
        qs.values("branch_id").annotate(c=Count("id")).values_list("branch_id", "c")
    )
    
    
    inside_map = dict(
        Member.objects.filter(gym_id=gym_id, branch_id__in=branch_ids, is_inside=True)
        .values("branch_id").annotate(c=Count("id")).values_list("branch_id", "c")
    )

    # income: ALL purchases this month (renewals count). This is correct for "income".
    income_map = dict(
        MemberSubscription.objects
        .filter(member__gym_id=gym_id, member__branch_id__in=branch_ids, created_at__gte=month_start, created_at__lte=now)
        .values("member__branch_id")
        .annotate(total=Sum("price_snapshot"))
        .values_list("member__branch_id", "total")
    )

    # ✅ expiring_7: count MEMBERS whose LATEST subscription ends within 7 days

    exp7_map = dict(
        Member.objects
        .filter(gym_id=gym_id, branch_id__in=branch_ids, is_active=True)
        .annotate(latest_end_at=Subquery(latest_sub.values("end_at")[:1]))
        .filter(latest_end_at__isnull=False, latest_end_at__gte=now, latest_end_at__lte=in_7)
        .values("branch_id")
        .annotate(c=Count("id"))
        .values_list("branch_id", "c")
    )

    rows = []
    for b in branches:
        bid = b["id"]
        rows.append({
            "branch_id": bid,
            "branch_name": b["name"],
            "active_members": int(active_map.get(bid, 0)),
            "inside_now": int(inside_map.get(bid, 0)),
            "income_month": int(income_map.get(bid, 0) or 0),
            "expiring_7": int(exp7_map.get(bid, 0)),
        })
    return rows

