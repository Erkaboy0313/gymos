from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import render,redirect
from users.models import Gym
from users.permissions import require_gym_membership,get_staff_scope
from branches.models import Branch
from dashboard.selectors import (
    income_by_month,
    members_new_by_month,
    members_left_by_month,
    income_month,
    active_members_now,
    inside_now,
    expiring_counts,
    branch_analytics_rows,
    branch_income_chart_data,
    branch_active_members_chart_data,
)

@login_required
def owner_dashboard_page(request, gym_id: int):
    # any staff can view; owners/admins care most, but keep it visible.
    gs = require_gym_membership(request.user, gym_id)
    gym = Gym.objects.get(id = gym_id)
    scope = get_staff_scope(gs)

    branch_param = request.GET.get("branch")
    branch_id = None

    if scope["forced_branch_id"]:
        branch_id = scope["forced_branch_id"]
    else:
        if branch_param and branch_param.isdigit():
            branch_id = int(branch_param)
            

    period = request.GET.get("period", "6")

    try:
        months = int(period)
        if months not in (3, 6, 12):
            months = 6
    except ValueError:
        months = 6


    branches = Branch.objects.filter(gym_id=gym_id).order_by("id")
    selected_branch = branches.filter(id=branch_id).first() if branch_id else None
    

    members_mode = request.GET.get("members", "total")  # total/new/left

    income_labels, income_values = income_by_month(gym_id, months, branch_id)

    new_labels, new_values = members_new_by_month(gym_id, months, branch_id)
    left_labels, left_values = members_left_by_month(gym_id, months, branch_id)

    # total series (v1): cumulative new - left
    total_values = []
    running = 0
    for n, l in zip(new_values, left_values):
        running += (n - l)
        total_values.append(max(0, running))

    if members_mode == "new":
        member_labels, member_values = new_labels, new_values
    elif members_mode == "left":
        member_labels, member_values = left_labels, left_values
    else:
        member_labels, member_values = new_labels, total_values  # use same labels

    exp_today, exp_7 = expiring_counts(gym_id,branch_id)

    context_branch_name = selected_branch.name if selected_branch else None
    context_branch_mode = "selected" if not scope["forced_branch_id"] else "assigned" if scope["forced_branch_id"] else None
    
    
    ctx = {
        "gym_id": gym_id,
        "gym": gym,
        "months": months,
        "members_mode": members_mode,
        
        "branch_id":branch_id,
        "branches":branches,
        "selected_branch":selected_branch,


        "income_this_month": income_month(gym_id, 0, branch_id),
        "income_last_month": income_month(gym_id, 1, branch_id),
        "active_members": active_members_now(gym_id, branch_id),
        "inside_now": inside_now(gym_id, branch_id),
        "exp_today": exp_today,
        "exp_7": exp_7,

        "income_labels": income_labels,
        "income_values": income_values,
        "member_labels": member_labels,
        "member_values": member_values,
        "branch_rows":branch_analytics_rows(gym_id),
        "context_branch_name":context_branch_name,
        "context_branch_mode":context_branch_mode
    }
    if not branch_id:
        income_branch_labels, income_branch_values = branch_income_chart_data(gym_id)
        members_branch_labels, members_branch_values = branch_active_members_chart_data(gym_id)

        ctx["branch_compare_income_labels"] = income_branch_labels
        ctx["branch_compare_income_values"] = income_branch_values
        ctx["branch_compare_members_labels"] = members_branch_labels
        ctx["branch_compare_members_values"] = members_branch_values
    else:
        ctx["branch_compare_income_labels"] = []
        ctx["branch_compare_income_values"] = []
        ctx["branch_compare_members_labels"] = []
        ctx["branch_compare_members_values"] = []
    return render(request, "app/gym_overview.html", ctx)


@require_POST
def update_branch_access_mode(request, gym_id: int):
    gs = require_gym_membership(request.user, gym_id)

    if gs.role not in ("owner", "admin"):
        return redirect(f"/api/dashboard/app/gyms/{gym_id}/?err=forbidden")

    mode = request.POST.get("mode")

    if mode not in ("all", "registered_only"):
        return redirect(f"/api/dashboard/app/gyms/{gym_id}/?err=bad_mode")

    Gym.objects.filter(id=gym_id).update(branch_access_mode=mode)

    return redirect(f"/api/dashboard/app/gyms/{gym_id}/?ok=branch_policy_updated")
