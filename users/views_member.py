from django.db.models import Q
from django.db import IntegrityError
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from datetime import timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from users.services import link_phone_to_telegram_across_gyms
from users.services import verify_tg_session,normalize_uz_phone
from users.permissions import require_gym_membership,get_staff_scope
from users.models import Member
from branches.models import Branch
from subscriptions.models import MemberPlan, MemberSubscription
from subscriptions.services import create_subscription, is_member_active
from access.models import EntryLog


@login_required
def members_page(request, gym_id: int):
    gs = require_gym_membership(request.user, gym_id)

    scope = get_staff_scope(gs)

    q = (request.GET.get("q") or "").strip()
    branch_id = request.GET.get("branch_id") or ""
    active = request.GET.get("active") or ""

    if scope["forced_branch_id"]:
        branch_id = scope["forced_branch_id"]

    branches = Branch.objects.filter(gym_id=gym_id, is_active=True).order_by("name")
    selected_branch = branches.filter(id=branch_id).first() if branch_id else None
    
    qs = Member.objects.filter(gym_id=gym_id).select_related("branch").order_by("-id")

    if q:
        qs = qs.filter(Q(full_name__icontains=q) | Q(phone__icontains=q))
    if branch_id:
        qs = qs.filter(branch_id=branch_id)
    if active in ("true", "false"):
        qs = qs.filter(is_active=(active == "true"))

    members = qs[:200]

    plans = MemberPlan.objects.filter(gym_id = gym_id)
    
    context_branch_name = selected_branch.name if selected_branch else None
    context_branch_mode = "selected" if not scope["forced_branch_id"] else "assigned" if scope["forced_branch_id"] else None
    
    return render(request, "app/members.html", {
        "gym_id": gym_id,
        "members": members,
        "branches": branches,
        "plans":plans,
        "q": q,
        "branch_id": branch_id,
        "active": active,
        "context_branch_name":context_branch_name,
        "context_branch_mode":context_branch_mode
    })

@login_required
def member_create(request, gym_id: int):
    gs = require_gym_membership(request.user, gym_id)
    
    scope = get_staff_scope(gs)
    
    if request.method != "POST":
        return redirect(f"/api/users/app/gyms/{gym_id}/members/")

    full_name = request.POST.get("full_name","").strip()
    phone_raw = request.POST.get("phone","").strip()
    branch_id = request.POST.get("branch_id",None) 
    plan_id = request.POST.get("plan_id",None) 
    
    if scope["forced_branch_id"]:
        branch_id = scope["forced_branch_id"]

    if not full_name or not phone_raw or not branch_id or not plan_id:
        return redirect(f"/api/users/app/gyms/{gym_id}/members/?err=missing")

    if branch_id:
        branch = Branch.objects.filter(id=branch_id, gym_id=gym_id).first()
        if not branch:
            return redirect(f"/api/users/app/gyms/{gym_id}/members/?err=wrong branch")

    if plan_id:
        plan = MemberPlan.objects.filter(id = plan_id, gym_id=gym_id).first()
        if not plan:
            return redirect(f"/api/users/app/gyms/{gym_id}/members/?err=wrong plan")

    try:
        phone = normalize_uz_phone(phone_raw)
    except Exception:
        return redirect(f"/api/users/app/gyms/{gym_id}/members/?err=bad_phone")
    
    # relies on DB constraint: unique phone per gym
    try:
        m = Member.objects.create(
            gym_id=gym_id,
            branch=branch,
            full_name=full_name,
            phone=phone,
            is_active=True,
        )
    except IntegrityError:
        return redirect(f"/api/users/app/gyms/{gym_id}/members/?err=duplicate_phone")
    create_subscription(member=m,plan=plan,start_at=timezone.now())
    return redirect(f"/api/users/app/gyms/{gym_id}/members/?ok=1")

@login_required
def member_update(request, gym_id: int, member_id: int):
    gs =require_gym_membership(request.user, gym_id)
    scope = get_staff_scope(gs)
    
    if request.method != "POST":
        return redirect(f"/api/users/app/gyms/{gym_id}/members/")

    m = Member.objects.filter(id=member_id, gym_id=gym_id).first()
    if not m:
        return redirect(f"/api/users/app/gyms/{gym_id}/members/?err=not_found")

    action = request.POST.get("action") or ""

    print(request.POST)

    if action == "toggle_block":
        m.is_active = not m.is_active
        m.save(update_fields=["is_active"])
        return redirect(f"/api/users/app/gyms/{gym_id}/members/?ok=1")

    full_name = (request.POST.get("full_name") or "").strip()
    phone = (request.POST.get("phone") or "").strip()
    branch_id = request.POST.get("branch_id") or None
    
    if scope["forced_branch_id"]:
        branch_id = scope["forced_branch_id"]
    
    if full_name:
        m.full_name = full_name
    if phone:
        m.phone = phone

    if branch_id:
        branch = Branch.objects.filter(id=branch_id, gym_id=gym_id).first()
        if not branch:
            return redirect(f"/api/users/app/gyms/{gym_id}/members/?err=bad_branch")
        m.branch = branch
    else:
        m.branch = None
    
    try:
        m.save(update_fields=["full_name", "phone", "branch"])
    except IntegrityError:
        return redirect(f"/api/users/app/gyms/{gym_id}/members/?err=duplicate_phone")
    
    return redirect(f"/api/users/app/gyms/{gym_id}/members/?ok=1")

@login_required
def member_detail_page(request, gym_id: int, member_id: int):
    require_gym_membership(request.user, gym_id)

    member = get_object_or_404(Member, id=member_id, gym_id=gym_id)
    plans = MemberPlan.objects.filter(gym_id=gym_id, is_active=True).order_by("duration_days", "price", "id")

    latest_sub = (
        MemberSubscription.objects
        .filter(member=member)
        .select_related("plan")
        .order_by("-start_at", "-id")
        .first()
    )

    logs = (
        EntryLog.objects
        .filter(gym_id=gym_id, member=member)
        .select_related("device", "branch")
        .order_by("-id")[:10]
    )

    now = timezone.now()
    ctx = {
        "gym_id": gym_id,
        "member": member,
        "plans": plans,
        "latest_sub": latest_sub,
        "is_active_now": is_member_active(member, now),
        "logs": logs,
        "now": now,
    }
    return render(request, "app/member_detail.html", ctx)

@login_required
def member_action(request, gym_id: int, member_id: int):
    require_gym_membership(request.user, gym_id)

    if request.method != "POST":
        return redirect(f"/api/users/app/gyms/{gym_id}/members/{member_id}/")

    member = get_object_or_404(Member, id=member_id, gym_id=gym_id)
    action = request.POST.get("action") or ""

    # ---------- block / unblock ----------
    if action == "toggle_block":
        member.is_active = not member.is_active
        member.save(update_fields=["is_active"])
        return redirect(f"/api/users/app/gyms/{gym_id}/members/{member_id}/?ok=1")

    # ---------- force checkout ----------
    if action == "force_checkout":
        member.is_inside = False
        member.inside_since = None
        member.save(update_fields=["is_inside", "inside_since"])
        return redirect(f"/api/users/app/gyms/{gym_id}/members/{member_id}/?ok=1")

    # ---------- renew / assign subscription ----------
    if action == "renew":
        plan_id = request.POST.get("plan_id")
        if not plan_id:
            return redirect(f"/api/users/app/gyms/{gym_id}/members/{member_id}/?err=missing_plan")

        plan = MemberPlan.objects.filter(id=plan_id, gym_id=gym_id, is_active=True).first()
        if not plan:
            return redirect(f"/api/users/app/gyms/{gym_id}/members/{member_id}/?err=bad_plan")

        # start now (v1)
        create_subscription(member, plan, start_at=timezone.now())
        return redirect(f"/api/users/app/gyms/{gym_id}/members/{member_id}/?ok=1")

    # ---------- freeze / unfreeze ----------
    latest_sub = (
        MemberSubscription.objects
        .filter(member=member)
        .order_by("-start_at", "-id")
        .first()
    )
    if action in ("freeze", "unfreeze") and not latest_sub:
        return redirect(f"/api/users/app/gyms/{gym_id}/members/{member_id}/?err=no_subscription")

    if action == "freeze":
        days = request.POST.get("freeze_days") or "7"
        try:
            days = int(days)
            if days <= 0:
                raise ValueError
        except ValueError:
            return redirect(f"/api/users/app/gyms/{gym_id}/members/{member_id}/?err=bad_freeze_days")

        latest_sub.frozen_until = timezone.now() + timedelta(days=days)
        latest_sub.save(update_fields=["frozen_until"])
        return redirect(f"/api/users/app/gyms/{gym_id}/members/{member_id}/?ok=1")

    if action == "unfreeze":
        latest_sub.frozen_until = None
        latest_sub.save(update_fields=["frozen_until"])
        return redirect(f"/api/users/app/gyms/{gym_id}/members/{member_id}/?ok=1")

    return redirect(f"/api/users/app/gyms/{gym_id}/members/{member_id}/?err=unknown_action")

class MyGymsView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        sess = request.headers.get("X-Member-Session")
        if not sess:
            return Response({"detail": "missing_member_session"}, status=401)

        try:
            payload = verify_tg_session(sess)
        except Exception:
            return Response({"detail": "invalid_member_session"}, status=401)

        tg_id = payload["tg"]

        qs = (
            Member.objects.filter(telegram_user_id=tg_id, is_active=True)
            .select_related("gym")
            .order_by("gym_id")
        )

        data = [
            {"gym_id": m.gym_id, "gym_name": m.gym.name, "member_id": m.id}
            for m in qs
        ]
        return Response(data, status=200)
    
class LinkPhoneView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        sess = request.headers.get("X-Member-Session")
        if not sess:
            return Response({"detail": "missing_member_session"}, status=401)

        try:
            payload = verify_tg_session(sess)
        except Exception:
            return Response({"detail": "invalid_member_session"}, status=401)

        phone = request.data.get("phone")
        if not phone:
            return Response({"detail": "phone required"}, status=400)

        tg_id = int(payload["tg"])
        result = link_phone_to_telegram_across_gyms(phone, tg_id)

        if result["not_found"]:
            return Response({"detail": "member_not_found"}, status=404)

        return Response(result, status=200)

