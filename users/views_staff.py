from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect
from django.db import IntegrityError
from branches.models import Branch
from users.permissions import require_gym_role
from users.models import GymStaff


@login_required
def staff_page(request, gym_id: int):
    gs = require_gym_role(request.user, gym_id, {GymStaff.ROLE_ADMIN, GymStaff.ROLE_OWNER})

    branches = Branch.objects.filter(gym_id = gym_id)

    staff = (
        GymStaff.objects
        .filter(gym_id=gym_id)
        .select_related("user")
        .order_by("-is_active", "role", "id")
    )

    if gs.role == GymStaff.ROLE_ADMIN:
        staff = staff.exclude(role = GymStaff.ROLE_OWNER)
    
    roles = tuple(filter(lambda x: x[0] != GymStaff.ROLE_OWNER, GymStaff.ROLE_CHOICES))

    return render(request, "app/staff.html", {
        "gym_id": gym_id,
        "staff": staff,
        "branches":branches,
        "roles":roles
    })


@login_required
def staff_action(request, gym_id: int):
    require_gym_role(request.user, gym_id, {GymStaff.ROLE_ADMIN, GymStaff.ROLE_OWNER})
    if request.method != "POST":
        return redirect(f"/api/users/app/gyms/{gym_id}/staff/")

    action = request.POST.get("action") or ""
    User = get_user_model()

    # --- add staff (by username; create user if missing) ---
    if action == "add":
        username = (request.POST.get("username") or "").strip()
        password = (request.POST.get("password") or "").strip()
        role = request.POST.get("role") or GymStaff.ROLE_STAFF
        branch_id = request.POST.get('branch_id',None)
        
        if role == GymStaff.ROLE_STAFF:
            if not branch_id:
                return redirect(f"/api/users/app/gyms/{gym_id}/staff/?err=missing_branch")
                
        if not username:
            return redirect(f"/api/users/app/gyms/{gym_id}/staff/?err=missing_username")

        if not password:
            return redirect(f"/api/users/app/gyms/{gym_id}/staff/?err=missing_password")
            
        
        if role not in (GymStaff.ROLE_OWNER, GymStaff.ROLE_ADMIN, GymStaff.ROLE_STAFF):
            return redirect(f"/api/users/app/gyms/{gym_id}/staff/?err=bad_role")

        user = User.objects.filter(username=username).first()
        
        if not user:

            user = User.objects.create_user(username=username, password=password)


        # prevent multiple owners
        if role == GymStaff.ROLE_OWNER:
            owner_exists = GymStaff.objects.filter(gym_id=gym_id, role=GymStaff.ROLE_OWNER, is_active=True).exists()
            if owner_exists:
                return redirect(f"/api/users/app/gyms/{gym_id}/staff/?err=owner_exists")

        branch = None
        if branch_id:
            try:
                branch = Branch.objects.get(id = branch_id)
            except Branch.DoesNotExist:
                return redirect(f"/api/users/app/gyms/{gym_id}/staff/?err=wrong_branch")
                
            
        # upsert GymStaff
        gs = GymStaff.objects.filter(gym_id=gym_id, user=user).first()
        if gs:
            gs.role = role
            gs.is_active = True
            gs.branch = branch
            gs.save(update_fields=["role", "is_active"])
        else:
            try:
                GymStaff.objects.create(gym_id=gym_id, user=user, role=role, is_active=True,branch = branch)
            except IntegrityError:
                return redirect(f"/api/users/app/gyms/{gym_id}/staff/?err=duplicate")

        return redirect(f"/api/users/app/gyms/{gym_id}/staff/?ok=1")

    # --- change role / toggle active / remove ---
    staff_id = request.POST.get("staff_id")
    if not staff_id:
        return redirect(f"/api/users/app/gyms/{gym_id}/staff/?err=missing_staff_id")

    gs = GymStaff.objects.filter(id=staff_id, gym_id=gym_id).select_related("user").first()
    if not gs:
        return redirect(f"/api/users/app/gyms/{gym_id}/staff/?err=not_found")

    # protect owner from accidental lockout
    # (do not allow deactivating the only active owner)
    if action in ("toggle_active", "remove", "set_role") and gs.role == GymStaff.ROLE_OWNER:
        active_owner_count = GymStaff.objects.filter(gym_id=gym_id, role=GymStaff.ROLE_OWNER, is_active=True).count()
        if active_owner_count <= 1:
            return redirect(f"/api/users/app/gyms/{gym_id}/staff/?err=cannot_change_last_owner")

    if action == "toggle_active":
        gs.is_active = not gs.is_active
        gs.save(update_fields=["is_active"])
        return redirect(f"/api/users/app/gyms/{gym_id}/staff/?ok=1")

    if action == "remove":
        gs.delete()
        return redirect(f"/api/users/app/gyms/{gym_id}/staff/?ok=1")

    return redirect(f"/api/users/app/gyms/{gym_id}/staff/?err=unknown_action")

@login_required
def update_staff(request, gym_id: int):
    require_gym_role(request.user, gym_id, {GymStaff.ROLE_ADMIN, GymStaff.ROLE_OWNER})
    if request.method == "POST":

        staff_id = request.POST.get("staff_id")
        if not staff_id:
            return redirect(f"/api/users/app/gyms/{gym_id}/staff/?err=missing_staff_id") 

        gs = GymStaff.objects.filter(id=staff_id, gym_id=gym_id).select_related("user").first()
        if not gs:
            return redirect(f"/api/users/app/gyms/{gym_id}/staff/?err=not_found")

        role = request.POST.get("role",None)

        branch_id = request.POST.get("branch_id",None)

        if role: 
            if not role in GymStaff.ROLE_CHOICES:
                return redirect(f"/api/users/app/gyms/{gym_id}/staff/?err=invalid_role")
            else:
                gs.role = role
        
        if branch_id:
            try:
                branch = Branch.objects.get(id = branch_id, gym_id =gym_id)
            except Branch.DoesNotExist:
                return redirect(f"/api/users/app/gyms/{gym_id}/staff/?err=invalid_branch")
            
            gs.branch = branch
        
        gs.save()

        return redirect(f"/api/users/app/gyms/{gym_id}/staff/?ok=1")

