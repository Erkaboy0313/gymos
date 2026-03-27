from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from users.permissions import require_gym_membership,require_gym_role,get_staff_scope
from datetime import timedelta
from django.utils import timezone
from users.models import Member
from subscriptions.models import MemberPlan, MemberSubscription
from subscriptions.services import create_subscription, is_member_active
from users.models import GymStaff
from django.db.models import Q
from branches.models import Branch

@login_required
def renew_center_page(request, gym_id: int):
    gs = require_gym_membership(request.user, gym_id)

    scope =get_staff_scope(gs)

    q = (request.GET.get("q") or "").strip()
    status = (request.GET.get("status") or "expiring").strip()   # expired / expiring / active / all
    days = request.GET.get("days") or "7"
    branch_id = request.GET.get("branch",None)

    try:
        days_i = int(days)
        if days_i < 0:
            days_i = 7
    except ValueError:
        days_i = 7

    # role-based branch restriction
    branches_qs = Branch.objects.filter(gym_id=gym_id, is_active=True).order_by("name")
    
    if scope['forced_branch_id']:
        selected_branch_id = scope['forced_branch_id']
    else:
        selected_branch_id = branch_id

    members_qs = (
        Member.objects
        .filter(gym_id=gym_id)
        .select_related("branch")
        .order_by("-id")
    )

    if selected_branch_id:
        members_qs = members_qs.filter(branch_id=selected_branch_id)

    if q:
        members_qs = members_qs.filter(
            Q(full_name__icontains=q) |
            Q(phone__icontains=q)
        )

    members = list(members_qs[:2000])
    member_ids = [m.id for m in members]

    latest_subs = {}
    subs = (
        MemberSubscription.objects
        .filter(member_id__in=member_ids)
        .select_related("plan", "member")
        .order_by("member_id", "-start_at", "-id")
    )

    for s in subs:
        if s.member_id not in latest_subs:
            latest_subs[s.member_id] = s

    today = request.user._meta.model.objects.none()  # dummy init to avoid accidental timezone import omission
    from django.utils import timezone
    today = timezone.localdate()
    until = today + timedelta(days=days_i)

    rows = []
    expired_count = 0
    expiring_count = 0
    active_count = 0

    for m in members:
        sub = latest_subs.get(m.id)
        if not sub:
            # should not happen now, but keep safe
            continue

        if sub.end_at < today:
            row_status = "expired"
            expired_count += 1
        elif today <= sub.end_at <= until:
            row_status = "expiring"
            expiring_count += 1
        else:
            row_status = "active"
            active_count += 1

        if status != "all" and row_status != status:
            continue

        rows.append({
            "member": m,
            "sub": sub,
            "status": row_status,
            "days_left": (sub.end_at - today).days,
        })
    
    status_priority = {
        "expired": 0,
        "expiring": 1,
        "active": 2,
    }

    rows.sort(
        key=lambda r: (
            status_priority.get(r["status"], 99),
            r["sub"].end_at,
            r["member"].full_name.lower(),
        )
    )

    plans = MemberPlan.objects.filter(gym_id=gym_id, is_active=True).order_by("duration_days", "price", "id")

    selected_branch = Branch.objects.filter(id=selected_branch_id).first() if selected_branch_id else None
    
    context_branch_name = selected_branch.name if selected_branch else None
    context_branch_mode = "selected" if not scope["forced_branch_id"] else "assigned" if scope["forced_branch_id"] else None
    
    return render(request, "app/renew_center.html", {
        "gym_id": gym_id,
        "rows": rows[:500],
        "plans": plans,
        "days": days_i,
        "q": q,
        "status": status,
        "branches": branches_qs,
        "selected_branch_id": selected_branch_id,
        "expired_count": expired_count,
        "expiring_count": expiring_count,
        "active_count": active_count,
        "total_count": expired_count + expiring_count + active_count,
        "is_admin_role": gs.role in (GymStaff.ROLE_OWNER, GymStaff.ROLE_ADMIN),
        "context_branch_name":context_branch_name,
        "context_branch_mode":context_branch_mode
    })

@login_required
def renew_center_action(request, gym_id: int):
    require_gym_membership(request.user, gym_id)
    if request.method != "POST":
        return redirect(f"/api/subscriptions/app/gyms/{gym_id}/renew/")

    member_id = request.POST.get("member_id")
    plan_id = request.POST.get("plan_id")
    if not member_id or not plan_id:
        return redirect(f"/api/subscriptions/app/gyms/{gym_id}/renew/?err=missing")

    m = Member.objects.filter(id=member_id, gym_id=gym_id).first()
    if not m:
        return redirect(f"/api/subscriptions/app/gyms/{gym_id}/renew/?err=bad_member")

    plan = MemberPlan.objects.filter(id=plan_id, gym_id=gym_id, is_active=True).first()
    if not plan:
        return redirect(f"/api/subscriptions/app/gyms/{gym_id}/renew/?err=bad_plan")

    create_subscription(m, plan, start_at=timezone.now())
    return redirect(f"/api/subscriptions/app/gyms/{gym_id}/renew/?ok=1")

@login_required
def member_plans_page(request, gym_id: int):
    require_gym_membership(request.user, gym_id)
    require_gym_role(request.user, gym_id, {GymStaff.ROLE_ADMIN, GymStaff.ROLE_OWNER})
    plans = MemberPlan.objects.filter(gym_id=gym_id).order_by("-id")
    return render(request, "app/member_plans.html", {
        "gym_id": gym_id,
        "plans": plans,
    })

@login_required
def member_plan_create(request, gym_id: int):
    require_gym_membership(request.user, gym_id)
    require_gym_role(request.user, gym_id, {GymStaff.ROLE_ADMIN, GymStaff.ROLE_OWNER})
    if request.method != "POST":
        return redirect(f"/api/subscriptions/app/gyms/{gym_id}/plans/")

    name = (request.POST.get("name") or "").strip()
    duration_days = request.POST.get("duration_days") or ""
    price = request.POST.get("price") or ""

    if not name or not duration_days or not price:
        return redirect(f"/api/subscriptions/app/gyms/{gym_id}/plans/?err=missing")

    try:
        duration_days = int(duration_days)
        price = int(price)
        if duration_days < 0 or price < 0:
            raise ValueError()
    except ValueError:
        return redirect(f"/api/subscriptions/app/gyms/{gym_id}/plans/?err=bad_number")

    MemberPlan.objects.create(
        gym_id=gym_id,
        name=name,
        duration_days=duration_days,
        price=price,
        is_active=True,
    )
    return redirect(f"/api/subscriptions/app/gyms/{gym_id}/plans/?ok=1")

@login_required
def member_subscriptions_page(request, gym_id: int):
    gs = require_gym_membership(request.user, gym_id)
    scope = get_staff_scope(gs)

    q = (request.GET.get("q") or "").strip()
    status = (request.GET.get("status") or "").strip()  # active/expired/future/all
    branch_id = request.GET.get("branch") or ""
    plan_id = request.GET.get("plan") or ""

    qs = (
        MemberSubscription.objects
        .filter(member__gym_id=gym_id)
        .select_related("member", "member__branch", "plan")
        .order_by("-created_at", "-id")
    )

    # branch scope
    branches = None
    selected_branch_id = None
    if scope["forced_branch_id"]:
        selected_branch_id = scope["forced_branch_id"]
        qs = qs.filter(member__branch_id=selected_branch_id)
    else:
        branches = Branch.objects.filter(gym_id=gym_id, is_active=True).order_by("name")
        if branch_id.isdigit():
            selected_branch_id = int(branch_id)
            qs = qs.filter(member__branch_id=selected_branch_id)

    if q:
        qs = qs.filter(
            Q(member__full_name__icontains=q) |
            Q(member__phone__icontains=q)
        )

    plans = MemberPlan.objects.filter(gym_id=gym_id).order_by("name")
    selected_plan_id = None
    if plan_id.isdigit():
        selected_plan_id = int(plan_id)
        qs = qs.filter(plan_id=selected_plan_id)

    today = timezone.localdate()
    if status == "active":
        qs = qs.filter(start_at__lte=today, end_at__gte=today)
    elif status == "expired":
        qs = qs.filter(end_at__lt=today)
    elif status == "future":
        qs = qs.filter(start_at__gt=today)

    rows = list(qs[:500])

    def row_status(sub):
        if sub.start_at > today:
            return "future"
        if sub.end_at < today:
            return "expired"
        return "active"

    for r in rows:
        r.ui_status = row_status(r)

    context_branch_name = None
    context_branch_mode = None
    if scope["forced_branch_id"] and gs.branch:
        context_branch_name = gs.branch.name
        context_branch_mode = "assigned"
    elif selected_branch_id and branches is not None:
        sb = branches.filter(id=selected_branch_id).first()
        if sb:
            context_branch_name = sb.name
            context_branch_mode = "selected"

    return render(request, "app/member_subscriptions.html", {
        "gym_id": gym_id,
        "rows": rows,
        "q": q,
        "status": status or "all",
        "branches": branches,
        "selected_branch_id": selected_branch_id,
        "plans": plans,
        "selected_plan_id": selected_plan_id,
        "is_admin_role": scope["is_admin"],
        "context_branch_name": context_branch_name,
        "context_branch_mode": context_branch_mode,
    })

