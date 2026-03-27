from django.urls import path
from branches.views import BranchListCreateView, BranchUpdateView

urlpatterns = [
    path("gyms/<int:gym_id>/branches/", BranchListCreateView.as_view()),
    path("gyms/<int:gym_id>/branches/<int:branch_id>/", BranchUpdateView.as_view()),
]


from branches.web_views import branches_page, branch_create, branch_update

urlpatterns += [
    path("app/gyms/<int:gym_id>/branches/", branches_page),
    path("app/gyms/<int:gym_id>/branches/create/", branch_create),
    path("app/gyms/<int:gym_id>/branches/<int:branch_id>/update/", branch_update),
]