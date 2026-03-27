from django.urls import path
from .views import MemberListCreateView, MemberUpdateView, MemberBlockView, home
from .views_member import MyGymsView,LinkPhoneView,members_page, member_create, member_update, member_detail_page, member_action
from .views_staff import staff_action,staff_page,update_staff



urlpatterns = [
    #API
    path("gyms/<int:gym_id>/members/", MemberListCreateView.as_view()),
    path("gyms/<int:gym_id>/members/<int:member_id>/", MemberUpdateView.as_view()),
    path("gyms/<int:gym_id>/members/<int:member_id>/block/", MemberBlockView.as_view()),
    
    # WEB APP
    path("", home), # GYM staff or admin only to redirect gym admin or admin page
    path("app/gyms/<int:gym_id>/members/", members_page), # member list page
    path("app/gyms/<int:gym_id>/members/create/", member_create), # member create url
    path("app/gyms/<int:gym_id>/members/<int:member_id>/update/", member_update), # member update url
    path("app/gyms/<int:gym_id>/members/<int:member_id>/", member_detail_page), # member deail url
    path("app/gyms/<int:gym_id>/members/<int:member_id>/action/", member_action), # memeber actions, block, unblock freeze, renew, checkout
    
    # WEB APP STAF    
    path("app/gyms/<int:gym_id>/staff/", staff_page),
    path("app/gyms/<int:gym_id>/staff/action/", staff_action),
    path("app/gyms/<int:gym_id>/staff/update/", update_staff),
    
    # WEB APP MEMBER
    path("me/gyms/", MyGymsView.as_view()), # my gyms list
    path("me/link-phone/", LinkPhoneView.as_view()), # link phone to see gyms
]
