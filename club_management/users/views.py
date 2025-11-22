# users/views.py
from django.urls import reverse
from django.contrib.auth import login, authenticate , logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .forms import CustomUserCreationForm, CustomAuthenticationForm
from .models import CustomUser
from clubs.models import Club, Membership
from Events.models import Event, Registration
from django.views.decorators.cache import never_cache
from django.contrib.auth import login, logout
from django.contrib import messages
from django.shortcuts import redirect, render
from .forms import CustomAuthenticationForm
from .decorators import admin_required , member_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count
from django.utils import timezone
from clubs.models import Club, Membership
from Events.models import Event, Registration
from Application.models import Application
from users.models import CustomUser
from django.core.paginator import Paginator

def loginPage(request):
    # If user already logged in
    if request.user.is_authenticated:
        messages.info(request, 'You are already logged in!')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        selected_role = request.POST.get('role')

        if form.is_valid():
            user = form.get_user()

            # If user's role doesn't match selected role
            if selected_role and hasattr(user, 'role') and user.role != selected_role:
                messages.error(request, 'Unknown user or incorrect role.')
                return redirect('login')

            # Role matches → allow login
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')

            # Redirect by role
            if user.role == 'member':
                return redirect('dashboard')
            elif user.role == 'admin':
                return redirect('admin_dashboard')
            else:
                return redirect('Landing')
        else:
            # Invalid username/password only
            messages.error(request, 'Invalid username or password.')

    else:
        form = CustomAuthenticationForm()

    return render(request, 'users/loginPage.html', {'form': form})

def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Registration successful! Welcome {user.personal_email}')
            return redirect('login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'users/SignUp.html', {'form': form})



@member_required
def dashboard_view(request):
    return render(request, 'users/dashboard.html')

@admin_required
def admin_dashboard(request):
    return render(request, 'admin/AdminPage.html')


def landingPage(request):
    # Get all active clubs to showcase on landing page
    clubs = Club.objects.all()[:6]  # Limit to 6 clubs for showcase
    
    # Get upcoming events
    upcoming_events = Event.objects.filter(
        start_time__gte=timezone.now()
    ).order_by('start_time')[:6]  # Limit to 6 upcoming events
    
    context = {
        'clubs': clubs,
        'upcoming_events': upcoming_events
    }
    return render(request, 'users/landingPage.html', context)

def logout_view(request):
    # Get user email before logout for message
    user_email = request.user.college_email if request.user.is_authenticated else None
    
    # Perform logout
    logout(request)
    
    # Success message
    if user_email:
        messages.success(request, f'You have been successfully logged out.')
    else:
        messages.info(request, 'You were already logged out.')
    
    return redirect('Landing')


# views.py
@login_required
def dashboard(request):
    if request.method == 'POST':
        college_email = (request.POST.get('college_email') or '').strip()
        course = request.POST.get('course')
        year = request.POST.get('year')
        branch = request.POST.get('branch')
        username = (request.POST.get('username') or '').strip()
        personal_email = (request.POST.get('personal_email') or '').strip()
        phone = (request.POST.get('phone') or '').strip()
        profile_picture = request.FILES.get('profile_picture')
        
        # Update user profile
        user = request.user
        # Handle unique nullable college_email safely
        if college_email:
            # Prevent duplicate unique value
            if CustomUser.objects.filter(college_email=college_email).exclude(pk=user.pk).exists():
                messages.error(request, 'That college email is already in use.')
                return redirect('dashboard')
            user.college_email = college_email
        else:
            # Store NULL instead of empty string to avoid UNIQUE collisions
            user.college_email = None
        if username:
            user.username = username
        if personal_email:
            user.personal_email = personal_email
        if phone:
            user.phone = phone
        if course:
            user.course = course
        if year:
            user.year = year
        if branch:
            user.branch = branch
        if profile_picture:
            user.profile_picture = profile_picture
        
        user.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('dashboard')
    
    # GET: assemble data for dashboard
    my_memberships = Membership.objects.filter(user=request.user, status='active').select_related('club')
    my_clubs = [m.club for m in my_memberships]
    my_club_ids = [c.id for c in my_clubs]

    available_clubs = Club.objects.filter(is_active=True).exclude(id__in=my_club_ids)
    
    # Get user's registered events
    user_registrations = Registration.objects.filter(user=request.user, status='registered').select_related('event', 'event__club')
    registered_event_ids = [reg.event.id for reg in user_registrations]
    registered_events = [reg.event for reg in user_registrations]
    
    # Exclude already registered events from upcoming events
    upcoming_events = Event.objects.filter(status__in=['upcoming', 'ongoing']).exclude(id__in=registered_event_ids).select_related('club').order_by('start_time')[:12]
    
    # Get user's applications
    user_applications = Application.objects.filter(user=request.user).select_related('club').order_by('-applied_date')
    pending_applications = user_applications.filter(status='pending')
    
    # Create a dictionary mapping club_id to application status for quick lookup
    club_application_status = {}
    for app in user_applications:
        if app.club.id not in club_application_status:
            club_application_status[app.club.id] = app.status
    
    # Annotate each club with its application status
    for club in available_clubs:
        club.application_status = club_application_status.get(club.id, None)

    return render(request, 'users/dashboard.html', {
        'my_clubs': my_clubs,
        'available_clubs': available_clubs,
        'upcoming_events': upcoming_events,
        'registered_events': registered_events,
        'user_applications': user_applications,
        'pending_applications': pending_applications,
        'club_application_status': club_application_status,
        'notifications': [],
    })


@login_required
def join_club(request):
    """Show application form for joining a club"""
    club_id = request.GET.get('club_id') or request.POST.get('club_id')
    if not club_id:
        messages.error(request, 'Club not specified.')
        return redirect('dashboard')
    
    try:
        club = Club.objects.get(pk=club_id, is_active=True)
    except Club.DoesNotExist:
        messages.error(request, 'Club not found.')
        return redirect('dashboard')
    
    # Check if user already has an active membership
    existing_membership = Membership.objects.filter(user=request.user, club=club, status='active').first()
    
    if existing_membership:
        messages.info(request, f'You are already a member of {club.name}.')
        return redirect('dashboard')
    
    # Check for any existing application (pending, approved, or rejected)
    existing_application = Application.objects.filter(user=request.user, club=club).first()
    
    if existing_application:
        if existing_application.status == 'pending':
            messages.info(request, f'You already have a pending application for {club.name}.')
            return redirect('dashboard')
        elif existing_application.status == 'approved':
            messages.info(request, f'Your application for {club.name} has been approved.')
            return redirect('dashboard')
        elif existing_application.status == 'rejected':
            # Allow reapplication if rejected, but update the existing application
            if request.method == 'POST':
                why_join = request.POST.get('why_join', '').strip()
                skills = request.POST.get('skills', '').strip()
                experience = request.POST.get('experience', '').strip()
                expectations = request.POST.get('expectations', '').strip()
                
                if not all([why_join, skills, expectations]):
                    messages.error(request, 'Please fill all required fields.')
                    return render(request, 'users/apply_club.html', {'club': club})
                
                # Update existing rejected application
                existing_application.why_join = why_join
                existing_application.skills = skills
                existing_application.experience = experience
                existing_application.expectations = expectations
                existing_application.status = 'pending'
                existing_application.applied_date = timezone.now()
                existing_application.save()
                
                messages.success(request, f'Your application for {club.name} has been resubmitted and is pending admin approval.')
                return redirect('dashboard')
    
    if request.method == 'POST':
        why_join = request.POST.get('why_join', '').strip()
        skills = request.POST.get('skills', '').strip()
        experience = request.POST.get('experience', '').strip()
        expectations = request.POST.get('expectations', '').strip()
        
        if not all([why_join, skills, expectations]):
            messages.error(request, 'Please fill all required fields.')
            return render(request, 'users/apply_club.html', {'club': club})
        
        # Create new application (only if no existing application found)
        try:
            application = Application.objects.create(
                user=request.user,
                club=club,
                why_join=why_join,
                skills=skills,
                experience=experience,
                expectations=expectations,
                status='pending'
            )
            messages.success(request, f'Your application for {club.name} has been submitted and is pending admin approval.')
        except Exception as e:
            messages.error(request, 'An error occurred while submitting your application. You may have already applied.')
        return redirect('dashboard')
    
    return render(request, 'users/apply_club.html', {'club': club})


@login_required
def leave_club(request):
    if request.method != 'POST':
        return redirect('dashboard')
    club_id = request.POST.get('club_id')
    Membership.objects.filter(user=request.user, club_id=club_id).delete()
    messages.success(request, 'Left the club.')
    return redirect('dashboard')


@login_required
def register_event(request):
    if request.method != 'POST':
        return redirect('dashboard')
    event_id = request.POST.get('event_id')
    try:
        ev = Event.objects.get(pk=event_id)
    except Event.DoesNotExist:
        messages.error(request, 'Event not found.')
        return redirect('dashboard')
    Registration.objects.get_or_create(event=ev, user=request.user)
    messages.success(request, 'Registered for the event.')
    return redirect('dashboard')


@login_required
def change_password(request):
    if request.method != 'POST':
        return redirect('dashboard')

    current_password = (request.POST.get('current_password') or '').strip()
    new_password = (request.POST.get('new_password') or '').strip()
    confirm_password = (request.POST.get('confirm_password') or '').strip()

    if not current_password or not new_password or not confirm_password:
        messages.error(request, 'All password fields are required.')
        

    if new_password != confirm_password:
        messages.error(request, 'New password and confirmation do not match.')
        

    user = request.user
    if not user.check_password(current_password):
        messages.error(request, 'Current password is incorrect.')
        

    try:
        validate_password(new_password, user=user)
    except ValidationError as e:
        # Show first few validation errors to user
        messages.error(request, '; '.join(e.messages[:3]))
        return redirect('dashboard')

    user.set_password(new_password)
    user.save()
    update_session_auth_hash(request, user)
    messages.success(request, 'Your password has been updated successfully.')
    return redirect('dashboard')

def admin_required(function):
    """Decorator to check if user is admin"""
    def wrap(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role in ['admin', 'superadmin']:
            return function(request, *args, **kwargs)
        else:
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('dashboard')
    return wrap

@login_required
@admin_required
def admin_dashboard(request):
    """Main admin dashboard"""
    # Handle profile update POST request
    if request.method == 'POST':
        college_email = request.POST.get('college_email', '').strip()
        enrollment_number = request.POST.get('enrollment_number', '').strip()
        course = request.POST.get('course')
        year = request.POST.get('year')
        branch = request.POST.get('branch')
        username = (request.POST.get('username') or '').strip()
        personal_email = (request.POST.get('personal_email') or '').strip()
        phone = (request.POST.get('phone') or '').strip()
        profile_picture = request.FILES.get('profile_picture')
        
        # Update user profile
        user = request.user
        # Handle unique nullable college_email safely
        if college_email:
            # Prevent duplicate unique value
            if CustomUser.objects.filter(college_email=college_email).exclude(pk=user.pk).exists():
                messages.error(request, 'That college email is already in use.')
                return redirect('admin_dashboard')
            user.college_email = college_email
        else:
            # Store NULL instead of empty string to avoid UNIQUE collisions
            user.college_email = None
        if username:
            user.username = username
        if personal_email:
            user.personal_email = personal_email
        if phone:
            user.phone = phone
        if course:
            user.course = course
        if year:
            user.year = year
        if branch:
            user.branch = branch
        if enrollment_number:
            user.enrollment_number = enrollment_number
        if profile_picture:
            user.profile_picture = profile_picture
        
        user.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('admin_dashboard#section-profile')
    
    # GET: Get statistics
    total_clubs = Club.objects.filter(is_active=True).count()
    total_users = CustomUser.objects.filter(is_active=True).count()
    total_events = Event.objects.exclude(status='cancelled').count()
    pending_applications = Application.objects.filter(status='pending').count()
    
    # Recent activities
    recent_clubs = Club.objects.order_by('-founded_date')[:5]
    recent_events = Event.objects.order_by('-created_at')[:5]
    recent_applications = Application.objects.order_by('-applied_date')[:5]
    
    context = {
        'total_clubs': total_clubs,
        'total_users': total_users,
        'total_events': total_events,
        'pending_applications': pending_applications,
        'recent_clubs': recent_clubs,
        'recent_events': recent_events,
        'recent_applications': recent_applications,
    }
    return render(request, 'admin_panel/admin_dashboard.html', context)

@login_required
@admin_required
def manage_clubs(request):
    """List all clubs with pagination"""
    clubs_list = Club.objects.annotate(
        member_count=Count('membership', filter=Q(membership__status='active'))
    ).order_by('-founded_date')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        clubs_list = clubs_list.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(clubs_list, 10)
    page_number = request.GET.get('page', 1)
    clubs = paginator.get_page(page_number)
    
    context = {
        'clubs': clubs,
        'search_query': search_query,
    }
    return render(request, 'admin_panel/manage_clubs.html', context)

@login_required
@admin_required
def add_club(request):
    """Add new club"""
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        contact_email = request.POST.get('contact_email')
        website = request.POST.get('website', '')
        logo = request.FILES.get('logo')
        
        if not all([name, description, contact_email]):
            messages.error(request, 'Please fill all required fields.')
            return render(request, 'admin_panel/add_club.html')
        
        try:
            club = Club.objects.create(
                name=name,
                description=description,
                contact_email=contact_email,
                website=website,
                logo=logo
            )
            messages.success(request, f'Club "{club.name}" created successfully!')
            return redirect('manage_club')
        except Exception as e:
            messages.error(request, f'Error creating club: {str(e)}')
    
    return render(request, 'admin_panel/add_club.html')

@login_required
@admin_required
def edit_club(request, club_id):
    """Edit existing club"""
    club = get_object_or_404(Club, id=club_id)
    
    if request.method == 'POST':
        club.name = request.POST.get('name')
        club.description = request.POST.get('description')
        club.contact_email = request.POST.get('contact_email')
        club.website = request.POST.get('website', '')
        
        if request.FILES.get('logo'):
            club.logo = request.FILES.get('logo')
        
        club.save()
        messages.success(request, f'Club "{club.name}" updated successfully!')
        return redirect('manage_club')
    
    context = {'club': club}
    return render(request, 'admin_panel/edit_club.html', context)

@login_required
@admin_required
def delete_club(request, club_id):
    """Soft delete club (set is_active to False)"""
    club = get_object_or_404(Club, id=club_id)
    
    if request.method == 'POST':
        club.is_active = False
        club.save()
        messages.success(request, f'Club "{club.name}" deactivated successfully!')
        return redirect('manage_club')
    
    context = {'club': club}
    return render(request, 'admin_panel/delete_club.html', context)

@login_required
@admin_required
def manage_users(request):
    """Manage all users"""
    users_list = CustomUser.objects.all().order_by('-date_joined')
    
    # Filter by role
    role_filter = request.GET.get('role', '')
    if role_filter:
        users_list = users_list.filter(role=role_filter)
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        users_list = users_list.filter(
            Q(username__icontains=search_query) |
            Q(personal_email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    paginator = Paginator(users_list, 10)
    page_number = request.GET.get('page', 1)
    users = paginator.get_page(page_number)
    
    context = {
        'users': users,
        'search_query': search_query,
        'role_filter': role_filter,
    }
    return render(request, 'admin_panel/manage_users.html', context)

@login_required
@admin_required
def user_profile(request, user_id):
    """View user profile details"""
    user = get_object_or_404(CustomUser, id=user_id)
    memberships = Membership.objects.filter(user=user).select_related('club')
    applications = Application.objects.filter(user=user).select_related('club')
    registrations = Registration.objects.filter(user=user).select_related('event')
    
    context = {
        'profile_user': user,
        'memberships': memberships,
        'applications': applications,
        'registrations': registrations,
    }
    return render(request, 'admin_panel/user_profile.html', context)

@login_required
@admin_required
def manage_applications(request):
    """Manage club membership applications"""
    status_filter = request.GET.get('status', '')
    applications_list = Application.objects.select_related('user', 'club').order_by('-applied_date')
    
    if status_filter:
        applications_list = applications_list.filter(status=status_filter)
    
    paginator = Paginator(applications_list, 10)
    page_number = request.GET.get('page', 1)
    applications = paginator.get_page(page_number)
    
    context = {
        'applications': applications,
        'status_filter': status_filter,
    }
    return render(request, 'admin_panel/manage_application.html', context)

@login_required
@admin_required
def review_application(request, application_id):
    """Review and approve/reject application"""
    application = get_object_or_404(Application, id=application_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        notes = request.POST.get('notes', '')
        
        if action == 'approve':
            application.status = 'approved'
            application.reviewed_by = request.user
            application.reviewed_date = timezone.now()
            application.notes = notes
            application.save()
            
            # Create membership
            Membership.objects.create(
                user=application.user,
                club=application.club,
                role='member',
                status='active'
            )
            messages.success(request, 'Application approved and membership created!')
            
        elif action == 'reject':
            application.status = 'rejected'
            application.reviewed_by = request.user
            application.reviewed_date = timezone.now()
            application.notes = notes
            application.save()
            messages.success(request, 'Application rejected.')
        
        return redirect('manage_applications')
    
    context = {'application': application}
    return render(request, 'admin_panel/review_application.html', context)

@login_required
@admin_required
def manage_events(request):
    """Manage all events with filtering"""
    events_list = Event.objects.select_related('club', 'created_by').order_by('-start_time')
    
    # Apply filters
    status_filter = request.GET.get('status', '')
    event_type_filter = request.GET.get('event_type', '')
    search_query = request.GET.get('search', '')
    
    if status_filter:
        events_list = events_list.filter(status=status_filter)
    
    if event_type_filter:
        events_list = events_list.filter(event_type=event_type_filter)
    
    if search_query:
        events_list = events_list.filter(
            Q(title__icontains=search_query) | 
            Q(description__icontains=search_query) |
            Q(club__name__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(events_list, 12)
    page_number = request.GET.get('page', 1)
    events = paginator.get_page(page_number)
    
    context = {
        'events': events,
    }
    return render(request, 'admin_panel/manage_events.html', context)

@login_required
@admin_required
def add_event(request):
    """Add new event"""
    clubs = Club.objects.filter(is_active=True)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        event_type = request.POST.get('event_type')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        location = request.POST.get('location')
        capacity = request.POST.get('capacity', 0)
        club_id = request.POST.get('club')
        image = request.FILES.get('image')
        is_public = request.POST.get('is_public') == 'on'
        
        try:
            event = Event.objects.create(
                title=title,
                description=description,
                event_type=event_type,
                start_time=start_time,
                end_time=end_time,
                location=location,
                capacity=capacity,
                club_id=club_id,
                created_by=request.user,
                image=image,
                is_public=is_public,
                status='upcoming'
            )
            messages.success(request, f'Event "{event.title}" created successfully!')
            return redirect('manage_events')
        except Exception as e:
            messages.error(request, f'Error creating event: {str(e)}')
    
    context = {'clubs': clubs}
    return render(request, 'admin_panel/add_events.html', context)

@login_required
@admin_required
def event_details(request, event_id):
    """View event details and registrations with comprehensive management"""
    event = get_object_or_404(Event, id=event_id)
    registrations = Registration.objects.filter(event=event).select_related('user').order_by('-registered_at')
    
    # Get club coordinators for assignment
    club_coordinators = Membership.objects.filter(
        club=event.club,
        role='coordinator',
        status='active'
    ).select_related('user')
    
    # Count registrations by status
    total_registered = registrations.filter(status='registered').count()
    total_attended = registrations.filter(status='attended').count()
    total_cancelled = registrations.filter(status='cancelled').count()
    
    context = {
        'event': event,
        'registrations': registrations,
        'club_coordinators': club_coordinators,
        'total_registered': total_registered,
        'total_attended': total_attended,
        'total_cancelled': total_cancelled,
        'is_admin': request.user.role == 'admin',
    }
    return render(request, 'admin_panel/event_details.html', context)

@login_required
@admin_required
def update_event(request, event_id):
    """Update event details (reschedule, change venue, assign coordinator)"""
    event = get_object_or_404(Event, id=event_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'reschedule':
            start_time = request.POST.get('start_time')
            end_time = request.POST.get('end_time')
            if start_time and end_time:
                event.start_time = start_time
                event.end_time = end_time
                event.save()
                messages.success(request, f'Event "{event.title}" has been rescheduled successfully.')
        
        elif action == 'change_venue':
            location = request.POST.get('location')
            if location:
                event.location = location
                event.save()
                messages.success(request, f'Venue for "{event.title}" has been updated.')
        
        elif action == 'update_capacity':
            capacity = request.POST.get('capacity')
            if capacity:
                event.capacity = int(capacity)
                event.save()
                messages.success(request, f'Capacity for "{event.title}" has been updated.')
        
        elif action == 'update_status':
            status = request.POST.get('status')
            if status:
                event.status = status
                event.save()
                messages.success(request, f'Status for "{event.title}" has been updated to {status}.')
        
        return redirect('event_details', event_id=event_id)
    
    return redirect('event_details', event_id=event_id)

@login_required
@admin_required
def print_registrations(request, event_id):
    """Generate printable list of registered members"""
    event = get_object_or_404(Event, id=event_id)
    registrations = Registration.objects.filter(
        event=event,
        status='registered'
    ).select_related('user').order_by('user__username')
    
    context = {
        'event': event,
        'registrations': registrations,
        'total_count': registrations.count(),
    }
    return render(request, 'admin_panel/print_registrations.html', context)

@login_required
def view_club_members(request, club_id):
    """View all members of a club - accessible to all authenticated users"""
    club = get_object_or_404(Club, id=club_id, is_active=True)
    
    # Get all active memberships for this club
    memberships = Membership.objects.filter(club=club, status='active').select_related('user').order_by('-role', 'join_date')
    
    # Group members by role
    leaders = [m for m in memberships if m.role == 'leader']
    coordinators = [m for m in memberships if m.role == 'coordinator']
    admins = [m for m in memberships if m.role == 'admin']
    members = [m for m in memberships if m.role == 'member']
    
    # Check if current user is admin (for role assignment)
    is_admin = request.user.is_authenticated and request.user.role in ['admin', 'superadmin']
    
    context = {
        'club': club,
        'memberships': memberships,
        'leaders': leaders,
        'coordinators': coordinators,
        'admins': admins,
        'members': members,
        'is_admin': is_admin,
    }
    return render(request, 'users/club_members.html', context)

@login_required
def get_user_profile_json(request, user_id):
    """Get user profile data as JSON for profile card"""
    try:
        user = CustomUser.objects.get(id=user_id)
        
        # Get user's memberships
        memberships = Membership.objects.filter(user=user, status='active').select_related('club')
        clubs = [{'name': m.club.name, 'role': m.role} for m in memberships]
        
        # Get course display name
        course_display = dict(CustomUser.COURSE_CHOICES).get(user.course, user.course) if user.course else None
        year_display = dict(CustomUser.YEAR_CHOICES).get(user.year, user.year) if user.year else None
        
        # Find coordinator/leader roles
        coordinator_clubs = [club for club in clubs if club['role'] in ['coordinator', 'leader', 'admin']]
        is_coordinator = len(coordinator_clubs) > 0
        coordinator_club_name = coordinator_clubs[0]['name'] if coordinator_clubs else None
        
        profile_data = {
            'id': user.id,
            'username': user.username,
            'full_name': user.get_full_name() or user.username,
            'role': user.role,
            'profile_picture': user.profile_picture.url if user.profile_picture else None,
            'personal_email': user.personal_email or user.email,
            'college_email': user.college_email,
            'phone': user.phone,
            'course': course_display,
            'year': year_display,
            'branch': user.branch or 'None',
            'enrollment_number': user.enrollment_number,
            'clubs': clubs,
            'is_coordinator': is_coordinator,
            'coordinator_club_name': coordinator_club_name,
            'coordinator_clubs': coordinator_clubs,
        }
        
        return JsonResponse(profile_data)
    except CustomUser.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)

@login_required
@admin_required
def assign_member_role(request, membership_id):
    """Admin can assign leader or coordinator role to a member"""
    membership = get_object_or_404(Membership, id=membership_id)
    
    if request.method == 'POST':
        new_role = request.POST.get('role')
        
        if new_role in ['member', 'coordinator', 'leader', 'admin']:
            old_role = membership.role
            membership.role = new_role
            membership.save()
            messages.success(request, f'{membership.user.username}\'s role has been changed from {old_role} to {new_role}.')
        else:
            messages.error(request, 'Invalid role selected.')
        
        return redirect('view_club_members', club_id=membership.club.id)
    
    return redirect('view_club_members', club_id=membership.club.id)