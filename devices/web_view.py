from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.db import IntegrityError

from users.permissions import require_gym_membership,require_gym_role,get_staff_scope
from branches.models import Branch
from devices.models import Device
from users.models import GymStaff


@login_required
def devices_page(request, gym_id: int):
    gs = require_gym_membership(request.user, gym_id)

    scope = get_staff_scope(gs)
    
    branches = Branch.objects.filter(gym_id=gym_id, is_active=True).order_by("name")

    branch_id = request.GET.get("branch_id") or ""
    
    if scope['forced_branch_id']:
        branch_id = scope['forced_branch_id']
    
    q = (request.GET.get("q") or "").strip()

    qs = Device.objects.filter(branch__gym_id=gym_id).select_related("branch").order_by("-id")
    if branch_id:
        qs = qs.filter(branch_id=branch_id)
    if q:
        qs = qs.filter(name__icontains=q)

    devices = qs[:200]
    selected_branch = branches.filter(id=branch_id).first() if branch_id else None
    context_branch_name = selected_branch.name if selected_branch else None
    context_branch_mode = "selected" if not scope["forced_branch_id"] else "assigned" if scope["forced_branch_id"] else None    
    return render(request, "app/devices.html", {
        "gym_id": gym_id,
        "branches": branches,
        "devices": devices,
        "branch_id": branch_id,
        "q": q,
        "modes": Device.MODE_CHOICES,
        "context_branch_name":context_branch_name,
        "context_branch_mode":context_branch_mode
    })


@login_required
def device_create(request, gym_id: int):
    require_gym_membership(request.user, gym_id)
    require_gym_role(request.user, gym_id, {GymStaff.ROLE_ADMIN, GymStaff.ROLE_OWNER})
    if request.method != "POST":
        return redirect(f"/api/devices/app/gyms/{gym_id}/devices/")

    name = (request.POST.get("name") or "").strip()
    branch_id = request.POST.get("branch_id")
    mode = request.POST.get("mode") or Device.MODE_KIOSK
    cooldown = request.POST.get("cooldown_seconds") or "300"

    if not name or not branch_id:
        return redirect(f"/api/devices/app/gyms/{gym_id}/devices/?err=missing")

    branch = Branch.objects.filter(id=branch_id, gym_id=gym_id).first()
    if not branch:
        return redirect(f"/api/devices/app/gyms/{gym_id}/devices/?err=bad_branch")

    try:
        cooldown_i = int(cooldown)
        if cooldown_i < 0:
            cooldown_i = 0
    except ValueError:
        return redirect(f"/api/devices/app/gyms/{gym_id}/devices/?err=bad_cooldown")

    Device.objects.create(
        branch=branch,
        name=name,
        mode=mode,
        cooldown_seconds=cooldown_i,
        is_active=True,
    )
    return redirect(f"/api/devices/app/gyms/{gym_id}/devices/?ok=1")


@login_required
def device_update(request, gym_id: int, device_id: int):
    require_gym_membership(request.user, gym_id)
    require_gym_role(request.user, gym_id, {GymStaff.ROLE_ADMIN, GymStaff.ROLE_OWNER})
    if request.method != "POST":
        return redirect(f"/api/devices/app/gyms/{gym_id}/devices/")

    d = Device.objects.filter(id=device_id, branch__gym_id=gym_id).select_related("branch").first()
    if not d:
        return redirect(f"/api/devices/app/gyms/{gym_id}/devices/?err=not_found")

    action = request.POST.get("action")

    if action == "toggle":
        d.is_active = not d.is_active
        d.save(update_fields=["is_active"])
        return redirect(f"/api/devices/app/gyms/{gym_id}/devices/?ok=1")

    # edit fields
    name = (request.POST.get("name") or "").strip()
    mode = request.POST.get("mode") or d.mode
    cooldown = request.POST.get("cooldown_seconds") or str(d.cooldown_seconds)

    if name:
        d.name = name
    d.mode = mode

    try:
        cooldown_i = int(cooldown)
        if cooldown_i < 0:
            cooldown_i = 0
        d.cooldown_seconds = cooldown_i
    except ValueError:
        return redirect(f"/api/devices/app/gyms/{gym_id}/devices/?err=bad_cooldown")

    d.save(update_fields=["name", "mode", "cooldown_seconds"])
    return redirect(f"/api/devices/app/gyms/{gym_id}/devices/?ok=1")