from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from users.permissions import require_gym_membership,require_gym_role
from branches.models import Branch
from users.models import GymStaff
from subscriptions.selectors import get_gym_features

@login_required
def branches_page(request, gym_id: int):
    require_gym_membership(request.user, gym_id)
    require_gym_role(request.user, gym_id, {GymStaff.ROLE_ADMIN, GymStaff.ROLE_OWNER})

    q = (request.GET.get("q") or "").strip()

    qs = Branch.objects.filter(gym_id=gym_id).order_by("-id")
    if q:
        qs = qs.filter(name__icontains=q)

    branches = qs[:200]

    return render(request, "app/branches.html", {
        "gym_id": gym_id,
        "branches": branches,
        "q": q,
    })


@login_required
def branch_create(request, gym_id: int):
    require_gym_membership(request.user, gym_id)
    require_gym_role(request.user, gym_id, {GymStaff.ROLE_ADMIN, GymStaff.ROLE_OWNER})
    if request.method != "POST":
        return redirect(f"/api/branches/app/gyms/{gym_id}/branches/")

    name = (request.POST.get("name") or "").strip()
    address = (request.POST.get("address") or "").strip()

    if not name:
        return redirect(f"/api/branches/app/gyms/{gym_id}/branches/?err=missing")

    features = get_gym_features(gym_id)
    current = Branch.objects.filter(gym_id=gym_id).count()

    if current >= features.max_branches:
        return redirect(f"/api/branches/app/gyms/{gym_id}/branches/?err=branch_limit_{features.max_branches}")
        
    Branch.objects.create(gym_id=gym_id, name=name, address=address, is_active=True)
    return redirect(f"/api/branches/app/gyms/{gym_id}/branches/?ok=1")


@login_required
def branch_update(request, gym_id: int, branch_id: int):
    require_gym_membership(request.user, gym_id)
    require_gym_role(request.user, gym_id, {GymStaff.ROLE_ADMIN, GymStaff.ROLE_OWNER})
    if request.method != "POST":
        return redirect(f"/api/branches/app/gyms/{gym_id}/branches/")

    b = Branch.objects.filter(id=branch_id, gym_id=gym_id).first()
    if not b:
        return redirect(f"/api/branches/app/gyms/{gym_id}/branches/?err=not_found")

    action = request.POST.get("action")

    if action == "toggle":
        b.is_active = not b.is_active
        b.save(update_fields=["is_active"])
        return redirect(f"/api/branches/app/gyms/{gym_id}/branches/?ok=1")

    name = (request.POST.get("name") or "").strip()
    address = (request.POST.get("address") or "").strip()

    if name:
        b.name = name
    b.address = address
    b.save(update_fields=["name", "address"])

    return redirect(f"/api/branches/app/gyms/{gym_id}/branches/?ok=1")