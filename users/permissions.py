from django.core.exceptions import PermissionDenied
from users.selectors import staff_membership
from .models import GymStaff


def require_gym_role(user, gym_id: int, roles: set[str]) -> GymStaff:
    gs = GymStaff.objects.filter(gym_id=gym_id, user=user, is_active=True).first()
    if not gs:
        raise PermissionDenied("not_gym_staff")
    if gs.role not in roles:
        raise PermissionDenied("insufficient_role")
    return gs


def require_gym_membership(user, gym_id: int):
    """
    Enforce that a staff user belongs to gym_id (active membership).
    Returns GymStaff membership if allowed, otherwise raises PermissionDenied.
    """
    ms = staff_membership(user, gym_id)
    if not ms:
        raise PermissionDenied("You do not have access to this gym.")
    return ms

def get_staff_scope(gs: GymStaff):
    """
    Returns:
      {
        "is_admin": bool,
        "forced_branch_id": int | None,
      }
    """
    is_admin = gs.role in (GymStaff.ROLE_OWNER, GymStaff.ROLE_ADMIN)
    return {
        "is_admin": is_admin,
        "forced_branch_id": None if is_admin else gs.branch_id,
    }

