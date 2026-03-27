from dataclasses import dataclass
from typing import Optional

# Use your real GymPlan.code values here (recommend: starter/growth/pro/lifetime)
@dataclass(frozen=True)
class SaaSFeatures:
    max_branches: int
    api_access: bool
    custom_branding: bool
    kiosk_api_mode: bool  # future: device API mode
    support_level: str    # "standard" | "priority" | "sla"


FEATURES_BY_PLAN_CODE = {
    "starter": SaaSFeatures(
        max_branches=1,
        api_access=False,
        custom_branding=False,
        kiosk_api_mode=False,
        support_level="standard",
    ),
    "growth": SaaSFeatures(
        max_branches=3,
        api_access=False,
        custom_branding=False,
        kiosk_api_mode=False,
        support_level="priority",
    ),
    "pro": SaaSFeatures(
        max_branches=10,
        api_access=True,
        custom_branding=True,
        kiosk_api_mode=True,
        support_level="sla",
    ),
    # Lifetime self-host still has limits; you can bump later
    "lifetime": SaaSFeatures(
        max_branches=10,
        api_access=True,
        custom_branding=True,
        kiosk_api_mode=True,
        support_level="standard",
    ),
}