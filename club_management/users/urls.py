from django.urls import path
from . import views
urlpatterns = [
    path('', views.landingPage, name="Landing"),
    path('login/', views.loginPage, name="login"),
    path('login/verify-otp/', views.verify_otp, name="verify_otp"),
    path('login/resend-otp/', views.resend_otp, name="resend_otp"),

    path('signup/', views.signup_view, name="signup"),
    path('logout/', views.logout_view, name="logout"),
    path('dashboard/', views.dashboard, name="dashboard"),
    path('dashboard/notifications/mark-read/', views.mark_notifications_read, name="mark_notifications_read"),
    path('dashboard/notification-preferences/', views.update_notification_preferences, name="notification_preferences"),

    # admin-page prefixed routes (changed from 'admin/' to 'admin-page/')
    path('admin-page/admin_dashboard/', views.admin_dashboard, name="admin_dashboard"),
    path('admin-page/get_event_media/<int:event_id>/', views.get_event_media, name="get_event_media"),
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
    path('admin-page/ManageFeedbacks/', views.manage_feedbacks, name="manage_feedbacks"),
    path('admin-page/delete_feedback/<int:feedback_id>/', views.delete_feedback, name='delete_feedback'),


    path('dashboard/join/', views.join_club, name="join_club"),
    path('dashboard/leave/', views.leave_club, name="leave_club"),
    path('dashboard/register-event/', views.register_event, name="register_event"),
    path('dashboard/change-password/', views.change_password, name="change_password"),
    path('dashboard/past-event/<int:event_id>/', views.past_event_details, name="past_event_details"),
    path('dashboard/past-event/<int:event_id>/feedback/', views.submit_event_feedback, name="submit_event_feedback"),
    
    # Club members views
    path('club/<int:club_id>/members/', views.view_club_members, name="view_club_members"),
    path('admin-page/assign-role/<int:membership_id>/', views.assign_member_role, name="assign_member_role"),
    path('admin-page/remove-member/<int:membership_id>/', views.remove_member, name="remove_member"),
    
    # Profile card API
    path('api/user-profile/<int:user_id>/', views.get_user_profile_json, name="get_user_profile_json"),
   
]