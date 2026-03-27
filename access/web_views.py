from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Q

from users.permissions import require_gym_membership,get_staff_scope
from access.models import EntryLog
from branches.models import Branch

@login_required
def recent_entries_page(request, gym_id: int):
    gs = require_gym_membership(request.user, gym_id)
    scope = get_staff_scope(gs)

    q = (request.GET.get("q") or "").strip()
    allow = request.GET.get("allow", "")
    reason = (request.GET.get("reason") or "").strip()
    branch_id = request.GET.get("branch_id",None) 

    qs = EntryLog.objects.filter(gym_id=gym_id).select_related("member", "device", "branch")

    if scope["forced_branch_id"]:
        branch_id = scope["forced_branch_id"]

    if branch_id:
        qs = qs.filter(branch_id = branch_id)
        
    if allow in ("true", "false"):
        qs = qs.filter(allow=(allow == "true"))

    if reason:
        qs = qs.filter(reason=reason)

    if q:
        qs = qs.filter(
            Q(member__full_name__icontains=q) |
            Q(member__phone__icontains=q) |
            Q(device__name__icontains=q)
        )

    logs = qs.order_by("-id")[:200]

    branches = Branch.objects.filter(gym_id=gym_id)
    selected_branch = branches.filter(id=branch_id).first() if branch_id else None
    context_branch_name = selected_branch.name if selected_branch else None
    context_branch_mode = "selected" if not scope["forced_branch_id"] else "assigned" if scope["forced_branch_id"] else None
    return render(request, "app/recent_entries.html", {
        "gym_id": gym_id,
        "logs": logs,
        "q": q,
        "allow": allow,
        "reason": reason,
        "branches": branches,
        "context_branch_name":context_branch_name,
        "context_branch_mode":context_branch_mode
    })