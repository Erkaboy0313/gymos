from django.urls import path
from subscriptions.views import MemberPlanListCreateView, MemberSubscriptionCreateView,GymPlanListCreateView,GymSubscriptionCreateView
from subscriptions.web_views import member_plans_page, member_plan_create, renew_center_action,renew_center_page,member_subscriptions_page

urlpatterns = [
    # api
    path("gyms/<int:gym_id>/plans/", MemberPlanListCreateView.as_view()),
    path("gyms/<int:gym_id>/subscriptions/", MemberSubscriptionCreateView.as_view()),
    path("gyms/<int:gym_id>/saas/plans/", GymPlanListCreateView.as_view()),
    path("gyms/<int:gym_id>/saas/subscriptions/", GymSubscriptionCreateView.as_view()),

    # web page
    path("app/gyms/<int:gym_id>/renew/action/", renew_center_action),
    path("app/gyms/<int:gym_id>/renew/", renew_center_page),
    path("app/gyms/<int:gym_id>/plans/create/", member_plan_create),
    path("app/gyms/<int:gym_id>/plans/", member_plans_page),
    path("app/gyms/<int:gym_id>/member-subscriptions/", member_subscriptions_page),
    
]

