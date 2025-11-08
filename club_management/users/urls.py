from django.urls import path
from . import views
urlpatterns = [
    path('', views.landingPage, name="Landing"),
    path('login/', views.loginPage, name="login"),
    path('signup/', views.signup_view, name="signup"),
    path('logout/', views.logout_view, name="logout"),
    path('dashboard/', views.dashboard, name="dashboard"),

    # admin-page prefixed routes (changed from 'admin/' to 'admin-page/')
    path('admin-page/admin_dashboard/', views.admin_dashboard, name="admin_dashboard"),
    path('admin-page/ManageClub/', views.manage_clubs, name="manage_club"),
    path('admin-page/AddClub/', views.add_club, name="add_club"),
    path('admin-page/EditClub/<int:club_id>/', views.edit_club, name='edit_club'),

    path('admin-page/delete_club/', views.delete_club, name="delete_club"),
    path('admin-page/ManageUsers/', views.manage_users, name="manage_users"),
    path('admin-page/ViewUserProfile/', views.user_profile, name="user_profile"),
    path('admin-page/ManageApplication/', views.manage_applications, name="manage_applications"),
    path('admin-page/review_application/<int:application_id>/', views.review_application, name="review_application"),
    path('admin-page/ManageEvents/', views.manage_events, name="manage_events"),
    path('admin-page/AddEvent/', views.add_event, name="add_event"),
    path('admin-page/EventDetail/<int:event_id>/', views.event_details, name="event_details"),
    path('admin-page/EventDetail/<int:event_id>/update/', views.update_event, name="update_event"),
    path('admin-page/EventDetail/<int:event_id>/registrations/print/', views.print_registrations, name="print_registrations"),

    path('dashboard/join/', views.join_club, name="join_club"),
    path('dashboard/leave/', views.leave_club, name="leave_club"),
    path('dashboard/register-event/', views.register_event, name="register_event"),
    path('dashboard/change-password/', views.change_password, name="change_password"),
    
    # Club members views
    path('club/<int:club_id>/members/', views.view_club_members, name="view_club_members"),
    path('admin-page/assign-role/<int:membership_id>/', views.assign_member_role, name="assign_member_role"),
    
    # Profile card API
    path('api/user-profile/<int:user_id>/', views.get_user_profile_json, name="get_user_profile_json"),
]