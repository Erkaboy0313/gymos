from typing import Optional
from django.db.models import QuerySet
from users.models import Gym, GymStaff
from branches.models import Branch
from .models import User,Member

def member_by_telegram(gym_id: int, telegram_user_id: int):
    return Member.objects.filter(
        gym_id=gym_id,
        telegram_user_id=telegram_user_id,
        is_active=True,
    ).first()

def gyms_for_user(user: User) -> QuerySet[Gym]: 
    return Gym.objects.filter(
        staff__user=user,
        staff__is_active=True,
        is_active=True,
    ).distinct()

def staff_membership(user: User, gym_id: int) -> Optional[GymStaff]:
    return GymStaff.objects.filter(
        user=user,
        gym_id=gym_id,
        is_active=True,
        gym__is_active=True,
    ).select_related("gym").first()

def branches_for_user(user: User, gym_id: int) -> QuerySet[Branch]:
    # Only branches of gyms the user belongs to
    return Branch.objects.filter(
        gym_id=gym_id,
        gym__staff__user=user,
        gym__staff__is_active=True,
        gym__is_active=True,
        is_active=True,
    ).distinct()
