# users/views.py
from django.urls import reverse
from django.contrib.auth import login, authenticate , logout, update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.utils import timezone
from datetime import datetime, timedelta
import random
from .forms import CustomUserCreationForm, CustomAuthenticationForm
from .models import CustomUser, EventNotification
from clubs.models import Club, Membership
from Events.models import Event, Registration, EventMedia, EventFeedback
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
from Events.models import Event, Registration, EventMedia
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
                messages.error(request, 'Invalid credentials.')
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
def verify_otp(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    pending_user_id = request.session.get('pending_user_id')
    pending_otp = request.session.get('pending_otp')
    otp_created_at_str = request.session.get('otp_created_at')
    
    if not pending_user_id or not pending_otp:
        messages.error(request, 'Session expired or invalid. Please login again.')
        return redirect('login')
        
    # Check expiry (10 minutes)
    otp_created_at = datetime.fromisoformat(otp_created_at_str)
    if timezone.now() > otp_created_at + timedelta(minutes=10):
        messages.error(request, 'OTP expired. Please request a new one.')
        # Clean up session but keep user ID for resend
        request.session.pop('pending_otp', None)
        
    if request.method == 'POST':
        user_otp = request.POST.get('otp')
        if not user_otp:
            messages.error(request, 'Please enter the OTP.')
        elif user_otp == pending_otp:
            # Correct OTP
            try:
                user = CustomUser.objects.get(pk=pending_user_id)
                user.is_active = True
                user.save()
                
                login(request, user)
                
                # Success message
                messages.success(request, f'Account verified successfully! Welcome, {user.username}!')
                
                # Clean up session
                del request.session['pending_otp']
                del request.session['pending_user_id']
                del request.session['otp_created_at']
                
                # Redirect by role
                if user.role == 'member':
                    return redirect('dashboard')
                elif user.role == 'admin':
                    return redirect('admin_dashboard')
                else:
                    return redirect('Landing')
            except CustomUser.DoesNotExist:
                messages.error(request, 'User not found.')
                return redirect('login')
        else:
            messages.error(request, 'Invalid OTP. Please try again.')
            
    return render(request, 'users/otp_verification.html')

def resend_otp(request):
    pending_user_id = request.session.get('pending_user_id')
    if not pending_user_id:
        messages.error(request, 'Session expired. Please login again.')
        return redirect('login')
        
    try:
        user = CustomUser.objects.get(pk=pending_user_id)
        otp = ''.join(random.choices('0123456789', k=6))
        request.session['pending_otp'] = otp
        request.session['otp_created_at'] = timezone.now().isoformat()
        
        # Send OTP via email
        subject = 'Verify Your account - Club Management System'
        message = f'Hello {user.username},\n\nYour new OTP for signup verification is: {otp}\n\nThis OTP will expire in 10 minutes.'
        from_email = 'noreply@clubmanagement.com'
        recipient_list = [user.personal_email]
        
        send_mail(subject, message, from_email, recipient_list)
        messages.success(request, f'A new OTP has been sent to {user.personal_email}.')
        return redirect('verify_otp')
    except Exception as e:
        messages.error(request, f'Error resending OTP: {str(e)}')
        return redirect('login')


def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            # Create user but set as inactive
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            
            # Generate OTP
            otp = ''.join(random.choices('0123456789', k=6))
            request.session['pending_otp'] = otp
            request.session['pending_user_id'] = user.pk
            request.session['otp_created_at'] = timezone.now().isoformat()
            
            # Send OTP via email
            subject = 'Verify Your account - Club Management System'
            message = f'Hello {user.username},\n\nYour OTP for signup verification is: {otp}\n\nThis OTP will expire in 10 minutes.'
            from_email = 'noreply@clubmanagement.com'
            recipient_list = [user.personal_email]
            
            try:
                send_mail(subject, message, from_email, recipient_list)
                messages.success(request, f'Registration successful! An OTP has been sent to {user.personal_email}. Please verify your account.')
                return redirect('verify_otp')
            except Exception as e:
                # If mail fails, we might want to still allow verify but warn? 
                # Or delete the user and ask to retry?
                # For now, let's keep the user (inactive) and let them try resend from verify page
                messages.warning(request, f'User created but error sending verification email: {str(e)}. Please try resending OTP.')
                return redirect('verify_otp')
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
    
    now = timezone.now()

    # Get user's registered events (used for "Past Events" participation + "Upcoming" exclusion)
    user_registrations = Registration.objects.filter(
        user=request.user,
        status='registered',
    ).select_related('event', 'event__club')
    registered_event_ids = [reg.event.id for reg in user_registrations]
    # Only show future registered events in the "My Registered Events" panel.
    registered_events = [
        reg.event for reg in user_registrations
        if reg.event.end_time >= now and reg.event.status != 'cancelled'
    ]

    # Upcoming events should be based on time, not just status field.
    upcoming_events = Event.objects.filter(
        status__in=['upcoming', 'ongoing'],
        end_time__gte=now,
    ).exclude(id__in=registered_event_ids).select_related('club').order_by('start_time')[:12]

    # Past/expired events: ended already (even if admin hasn't updated `status` to "completed")
    happened_events_qs = Event.objects.filter(
        ~Q(status='cancelled'),
    ).filter(
        Q(end_time__lt=now) | Q(status='completed')
    ).select_related('club').order_by('-start_time')[:24]

    # Annotate per-event UI flags used by the template.
    user_registered_set = set(registered_event_ids)  # status='registered' => participated in your current feedback logic
    feedback_event_ids = set(EventFeedback.objects.filter(user=request.user, event_id__in=[e.id for e in happened_events_qs]).values_list('event_id', flat=True))

    happened_events = []
    for e in happened_events_qs:
        e.user_registered = e.id in user_registered_set
        e.user_gave_feedback = e.id in feedback_event_ids
        happened_events.append(e)
    
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

    assigned_club = None
    events_for_media = Event.objects.none()
    if request.user.role in ['admin', 'superadmin']:
        assigned_club = get_admin_assigned_club(request.user)
        if assigned_club:
            events_for_media = Event.objects.filter(
                club=assigned_club,
            ).exclude(status='cancelled').select_related('club').order_by('-created_at')[:50]

    photo_items = EventMedia.objects.filter(
        event__club_id__in=my_club_ids,
        media_type='photo',
    ).select_related('event', 'event__club').order_by('-uploaded_at')[:24]

    video_items = EventMedia.objects.filter(
        event__club_id__in=my_club_ids,
        media_type='video',
    ).select_related('event', 'event__club').order_by('-uploaded_at')[:24]

    can_upload_media = request.user.role in ['admin', 'superadmin'] and assigned_club is not None

    # Group media by event for the gallery
    participated_events_with_media = []
    # Filter events belonging to user's clubs
    club_events_with_media = Event.objects.filter(
        club_id__in=my_club_ids
    ).prefetch_related('media_items').distinct()

    for event in club_events_with_media:
        media_qs = event.media_items.all()
        if media_qs.exists():
            participated_events_with_media.append({
                'event': event,
                'photos': media_qs.filter(media_type='photo'),
                'videos': media_qs.filter(media_type='video'),
            })

    notifications = EventNotification.objects.filter(user=request.user).select_related('club', 'event').order_by('-created_at')[:10]
    unread_notifications_count = EventNotification.objects.filter(user=request.user, is_read=False).count()

    return render(request, 'users/dashboard.html', {
        'my_clubs': my_clubs,
        'available_clubs': available_clubs,
        'upcoming_events': upcoming_events,
        'registered_events': registered_events,
        'happened_events': happened_events,
        'user_applications': user_applications,
        'pending_applications': pending_applications,
        'club_application_status': club_application_status,
        'notifications': notifications,
        'unread_notifications_count': unread_notifications_count,
        'assigned_club': assigned_club,
        'events_for_media': events_for_media,
        'can_upload_media': can_upload_media,
        'participated_events_with_media': participated_events_with_media,
    })


@login_required
def mark_notifications_read(request):
    if request.method != 'POST':
        return redirect('dashboard')

    EventNotification.objects.filter(user=request.user).update(is_read=True)
    return redirect('dashboard')


@login_required
def update_notification_preferences(request):
    if request.method != 'POST':
        return redirect('dashboard')

    email_event_notifications = request.POST.get('email_event_notifications') == 'on'
    request.user.email_event_notifications = email_event_notifications
    request.user.save(update_fields=['email_event_notifications'])

    if email_event_notifications:
        messages.success(request, 'Event notification preferences updated.')
    else:
        messages.info(request, 'Event notifications turned off.')

    return redirect('dashboard')


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
    payment_method = request.POST.get('payment_method', '').strip()
    try:
        ev = Event.objects.get(pk=event_id)
    except Event.DoesNotExist:
        messages.error(request, 'Event not found.')
        return redirect('dashboard')

    registration, created = Registration.objects.get_or_create(event=ev, user=request.user)
    if not created and registration.status == 'registered' and registration.is_paid:
        messages.info(request, 'You are already registered for this event.')
        return redirect('dashboard')

    if ev.entry_fee and ev.entry_fee > 0:
        if not payment_method:
            messages.error(request, 'Please select a payment method before confirming registration.')
            return redirect('dashboard')
        registration.payment_method = payment_method
        registration.is_paid = payment_method != 'Pay at Event'
        registration.amount_paid = ev.entry_fee if registration.is_paid else 0.00
        registration.paid_at = timezone.now() if registration.is_paid else None
    
    registration.status = 'registered'
    registration.save()

    messages.success(request, 'Registered for the event successfully.')
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


def is_superadmin(user):
    return getattr(user, 'role', None) == 'superadmin'


def get_admin_assigned_club(user):
    """
    Resolve which club this admin manages.
    Priority:
    1) Explicit `CustomUser.assigned_club`
    2) Active Membership with role='admin'
    """
    if getattr(user, 'assigned_club_id', None):
        return user.assigned_club

    membership = Membership.objects.filter(
        user=user,
        role='admin',
        status='active',
    ).select_related('club').first()
    return membership.club if membership else None

@login_required
@admin_required
def admin_dashboard(request):
    """Main admin dashboard"""
    if request.method == 'POST':
        # Media upload from the MEDIA sidebar section
        if request.POST.get('form_type') == 'media_upload':
            superadmin = is_superadmin(request.user)
            assigned_club = None if superadmin else get_admin_assigned_club(request.user)

            event_id = request.POST.get('event_id')
            title = (request.POST.get('title') or '').strip()
            media_file = request.FILES.get('media_file')

            def form_response(success, message, status=200):
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': success, 'message': message}, status=status)
                if success:
                    messages.success(request, message)
                else:
                    messages.error(request, message)
                return redirect('admin_dashboard#section-media')

            if not event_id or not media_file:
                return form_response(False, 'Missing event or media file.', 400)

            event = get_object_or_404(Event, pk=event_id)

            if not superadmin:
                if not assigned_club or event.club_id != assigned_club.id:
                    return form_response(False, 'You can only upload media for your assigned club.', 403)

            content_type = (media_file.content_type or '').lower()
            media_type = None

            if content_type.startswith('image/'):
                media_type = 'photo'
            elif content_type.startswith('video/'):
                media_type = 'video'
            else:
                # Fallback by file extension
                filename = (media_file.name or '').lower()
                if filename.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                    media_type = 'photo'
                elif filename.endswith(('.mp4', '.mov', '.webm', '.mkv', '.avi', '.mpeg')):
                    media_type = 'video'

            if media_type not in ['photo', 'video']:
                return form_response(False, 'Unsupported media type. Upload a photo or a video.', 400)

            EventMedia.objects.create(
                event=event,
                uploaded_by=request.user,
                file=media_file,
                media_type=media_type,
                title=title,
            )
            return form_response(True, 'Multimedia uploaded successfully!')

        # Otherwise: Handle profile update POST request
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

    # GET: Get statistics + dashboard panels
    superadmin = is_superadmin(request.user)
    assigned_club = None if superadmin else get_admin_assigned_club(request.user)

    if superadmin:
        total_clubs = Club.objects.filter(is_active=True).count()
        total_users = CustomUser.objects.filter(is_active=True).count()
        total_events = Event.objects.exclude(status='cancelled').count()
        pending_applications = Application.objects.filter(status='pending').count()

        recent_clubs = Club.objects.order_by('-founded_date')[:5]
        recent_events = Event.objects.select_related('club').order_by('-created_at')[:5]
        recent_applications = Application.objects.select_related('user', 'club').order_by('-applied_date')[:5]

        recent_transactions = Application.objects.select_related('user', 'club').order_by('-applied_date')[:10]
        all_events = Event.objects.select_related('club').exclude(status='cancelled').order_by('-created_at')

        # Feedbacks
        feedbacks = EventFeedback.objects.all()
        recent_feedbacks = feedbacks.select_related('user', 'event').order_by('-submitted_at')[:5]
        feedback_stats = {i: feedbacks.filter(rating=i).count() for i in range(1, 6)}
    else:
        if assigned_club:
            total_clubs = 1
            total_users = CustomUser.objects.filter(
                membership__club=assigned_club,
                membership__status='active',
                is_active=True,
            ).distinct().count()
            total_events = Event.objects.filter(club=assigned_club).exclude(status='cancelled').count()
            pending_applications = Application.objects.filter(club=assigned_club, status='pending').count()

            recent_clubs = [assigned_club]
            recent_events = Event.objects.filter(club=assigned_club).select_related('club').order_by('-created_at')[:5]
            recent_applications = Application.objects.filter(club=assigned_club).select_related('user', 'club').order_by('-applied_date')[:5]

            recent_transactions = Application.objects.filter(club=assigned_club).select_related('user', 'club').order_by('-applied_date')[:10]
            all_events = Event.objects.filter(club=assigned_club).exclude(status='cancelled').select_related('club').order_by('-created_at')

            # Feedbacks
            feedbacks = EventFeedback.objects.filter(event__club=assigned_club)
            recent_feedbacks = feedbacks.select_related('user', 'event').order_by('-submitted_at')[:5]
            feedback_stats = {i: feedbacks.filter(rating=i).count() for i in range(1, 6)}
        else:
            total_clubs = 0
            total_users = 0
            total_events = 0
            pending_applications = 0

            recent_clubs = []
            recent_events = []
            recent_applications = []

            recent_transactions = Application.objects.none()
            all_events = Event.objects.none()
            
            recent_feedbacks = []
            feedback_stats = {i: 0 for i in range(1, 6)}

    context = {
        'assigned_club': assigned_club,
        'total_clubs': total_clubs,
        'total_users': total_users,
        'total_events': total_events,
        'pending_applications': pending_applications,
        'recent_clubs': recent_clubs,
        'recent_events': recent_events,
        'recent_applications': recent_applications,
        'recent_transactions': recent_transactions,
        'all_events': all_events,
        'recent_feedbacks': recent_feedbacks,
        'feedback_stats': feedback_stats,
    }
    return render(request, 'admin_panel/admin_dashboard.html', context)

@login_required
@admin_required
def get_event_media(request, event_id):
    """AJAX endpoint to get media for a specific event"""
    superadmin = is_superadmin(request.user)
    assigned_club = None if superadmin else get_admin_assigned_club(request.user)

    try:
        event = get_object_or_404(Event, pk=event_id)

        # Check if admin has access to this event
        if not superadmin and (not assigned_club or event.club_id != assigned_club.id):
            return JsonResponse({'error': 'Access denied'}, status=403)

        photos = EventMedia.objects.filter(event=event, media_type='photo').order_by('-uploaded_at')
        videos = EventMedia.objects.filter(event=event, media_type='video').order_by('-uploaded_at')

        photo_data = [{
            'id': media.id,
            'title': media.title or media.event.title,
            'file_url': media.file.url,
            'uploaded_at': media.uploaded_at.strftime('%Y-%m-%d %H:%M'),
        } for media in photos]

        video_data = [{
            'id': media.id,
            'title': media.title or media.event.title,
            'file_url': media.file.url,
            'uploaded_at': media.uploaded_at.strftime('%Y-%m-%d %H:%M'),
        } for media in videos]

        return JsonResponse({
            'event': {
                'id': event.id,
                'title': event.title,
                'club_name': event.club.name,
                'start_time': event.start_time.strftime('%Y-%m-%d %H:%M'),
            },
            'photos': photo_data,
            'videos': video_data,
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@admin_required
def manage_clubs(request):
    """List all clubs with pagination"""
    superadmin = is_superadmin(request.user)
    assigned_club = None if superadmin else get_admin_assigned_club(request.user)

    clubs_list = Club.objects.all()
    if not superadmin:
        if not assigned_club:
            clubs_list = Club.objects.none()
        else:
            clubs_list = Club.objects.filter(pk=assigned_club.pk)

    clubs_list = clubs_list.annotate(
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
        'is_superadmin': superadmin,
    }
    return render(request, 'admin_panel/manage_clubs.html', context)

@login_required
@admin_required
def add_club(request):
    """Add new club"""
    if not is_superadmin(request.user):
        messages.error(request, 'Only superadmins can add new clubs.')
        return redirect('admin_dashboard')

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

            recipients = CustomUser.objects.filter(is_active=True, email_event_notifications=True)
            EventNotification.objects.bulk_create([
                EventNotification(
                    user=u,
                    club=club,
                    event=None,
                    title='New Club Created',
                    message=f'Club "{club.name}" has been created.'
                )
                for u in recipients
            ], batch_size=500)
            return redirect('manage_club')
        except Exception as e:
            messages.error(request, f'Error creating club: {str(e)}')
    
    return render(request, 'admin_panel/add_club.html')

@login_required
@admin_required
def edit_club(request, club_id):
    """Edit existing club"""
    club = get_object_or_404(Club, id=club_id)
    if not is_superadmin(request.user):
        assigned_club = get_admin_assigned_club(request.user)
        if not assigned_club or club.id != assigned_club.id:
            messages.error(request, 'You can only edit your assigned club.')
            return redirect('admin_dashboard')
    
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
    if not is_superadmin(request.user):
        messages.error(request, 'Only superadmins can delete clubs.')
        return redirect('admin_dashboard')
    
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
            
            # Create or activate membership for approved application
            membership, created = Membership.objects.update_or_create(
                user=application.user,
                club=application.club,
                defaults={
                    'role': 'member',
                    'status': 'active'
                }
            )
            if not created and membership.status != 'active':
                membership.status = 'active'
                membership.save()
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
        entry_fee = request.POST.get('entry_fee', '0.00')
        payment_option = request.POST.get('payment_option', 'online')
        
        try:
            # Automate club assignment if user has an assigned_club
            assigned_club = getattr(request.user, 'assigned_club', None)
            final_club_id = assigned_club.id if assigned_club else club_id

            event = Event.objects.create(
                title=title,
                description=description,
                event_type=event_type,
                start_time=start_time,
                end_time=end_time,
                location=location,
                capacity=capacity,
                club_id=final_club_id,
                created_by=request.user,
                image=image,
                entry_fee=entry_fee,
                payment_option=payment_option,
                is_public=is_public,
                status='upcoming'
            )
            messages.success(request, f'Event "{event.title}" created successfully!')

            event_club = event.club
            recipients = CustomUser.objects.filter(is_active=True, email_event_notifications=True)
            EventNotification.objects.bulk_create([
                EventNotification(
                    user=u,
                    club=event_club,
                    event=event,
                    title='New Event Created',
                    message=f'New event "{event.title}" has been created for club "{event_club.name}".'
                )
                for u in recipients
            ], batch_size=500)
            return redirect('manage_events')
        except Exception as e:
            messages.error(request, f'Error creating event: {str(e)}')
    
    assigned_club = getattr(request.user, 'assigned_club', None)
    context = {
        'clubs': clubs,
        'assigned_club': assigned_club
    }
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

@login_required
@admin_required
def remove_member(request, membership_id):
    """Remove a member from a club and update dashboards accordingly."""
    membership = get_object_or_404(Membership, id=membership_id, status='active')
    superadmin = is_superadmin(request.user)
    assigned_club = None if superadmin else get_admin_assigned_club(request.user)

    if not superadmin and (not assigned_club or membership.club != assigned_club):
        messages.error(request, 'You do not have permission to remove this member.')
        return redirect('view_club_members', club_id=membership.club.id)

    if request.method == 'POST':
        if membership.user == request.user:
            messages.error(request, 'You cannot remove yourself from the club here.')
            return redirect('view_club_members', club_id=membership.club.id)

        member_name = membership.user.get_full_name() or membership.user.username
        club_name = membership.club.name
        membership.delete()
        messages.success(request, f'{member_name} has been removed from {club_name}. They can now reapply to the club from their dashboard.')

    return redirect('view_club_members', club_id=membership.club.id)


from Events.models import EventFeedback

@login_required
def submit_event_feedback(request, event_id):
    """Allow a member to submit feedback for a past event they attended"""
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    now = timezone.now()
    event = get_object_or_404(
        Event.objects.exclude(status='cancelled'),
        id=event_id,
        end_time__lt=now,
    )

    # Must be registered for the event
    if not Registration.objects.filter(event=event, user=request.user, status='registered').exists():
        if is_ajax:
            return JsonResponse({'error': 'You can only submit feedback for events you attended.'}, status=403)
        messages.error(request, 'You can only submit feedback for events you attended.')
        return redirect('dashboard')

    # Prevent duplicate feedback
    if EventFeedback.objects.filter(event=event, user=request.user).exists():
        if is_ajax:
            return JsonResponse({'error': 'You have already submitted feedback for this event.'}, status=400)
        messages.info(request, 'You have already submitted feedback for this event.')
        return redirect('past_event_details', event_id=event_id)

    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment', '').strip()

        if not rating or not rating.isdigit() or int(rating) not in range(1, 6):
            if is_ajax:
                return JsonResponse({'error': 'Please provide a valid rating between 1 and 5.'}, status=400)
            messages.error(request, 'Please provide a valid rating between 1 and 5.')
            return render(request, 'users/submit_feedback.html', {'event': event})

        feedback = EventFeedback.objects.create(
            event=event,
            user=request.user,
            rating=int(rating),
            comment=comment,
        )
        if is_ajax:
            return JsonResponse({
                'feedback': {
                    'rating': feedback.rating,
                    'comment': feedback.comment,
                    'user_name': feedback.user.get_full_name() or feedback.user.username,
                }
            })

        messages.success(request, 'Thank you for your feedback!')
        return redirect('past_event_details', event_id=event_id)

    # Should not be called with GET via the modal, but keep a safe fallback.
    if is_ajax:
        return JsonResponse({'error': 'Invalid request.'}, status=405)
    return render(request, 'users/submit_feedback.html', {'event': event})


@login_required
@admin_required
def manage_feedbacks(request):
    """Admin view to see all event feedbacks"""
    superadmin = is_superadmin(request.user)
    assigned_club = None if superadmin else get_admin_assigned_club(request.user)

    if superadmin:
        feedbacks = EventFeedback.objects.select_related('event', 'event__club', 'user').order_by('-submitted_at')
    elif assigned_club:
        feedbacks = EventFeedback.objects.filter(
            event__club=assigned_club
        ).select_related('event', 'event__club', 'user').order_by('-submitted_at')
    else:
        feedbacks = EventFeedback.objects.none()

    paginator = Paginator(feedbacks, 20)
    page_number = request.GET.get('page', 1)
    feedbacks_page = paginator.get_page(page_number)

    return render(request, 'admin_panel/manage_feedbacks.html', {
        'feedbacks': feedbacks_page,
        'is_superadmin': superadmin,
        'assigned_club': assigned_club,
    })


@login_required
@admin_required
def delete_feedback(request, feedback_id):
    """Admin can delete a feedback entry"""
    feedback = get_object_or_404(EventFeedback, id=feedback_id)
    superadmin = is_superadmin(request.user)
    assigned_club = None if superadmin else get_admin_assigned_club(request.user)

    if not superadmin and (not assigned_club or feedback.event.club != assigned_club):
        messages.error(request, 'You do not have permission to delete this feedback.')
        return redirect('manage_feedbacks')

    if request.method == 'POST':
        feedback.delete()
        messages.success(request, 'Feedback deleted successfully.')

    return redirect('manage_feedbacks')


@login_required
def past_event_details(request, event_id):
    """Show details of a past/completed event for a member"""
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    now = timezone.now()
    event = get_object_or_404(
        Event.objects.exclude(status='cancelled'),
        id=event_id,
        end_time__lt=now,
    )

    registration = Registration.objects.filter(event=event, user=request.user, status='registered').first()
    if not registration and not is_ajax:
        messages.error(request, 'You did not attend this event.')
        return redirect('dashboard')

    if is_ajax:
        existing_feedback = EventFeedback.objects.filter(event=event, user=request.user).first()
        can_give_feedback = registration is not None and existing_feedback is None

        feedbacks_qs = (
            EventFeedback.objects.filter(event=event)
            .select_related('user')
            .order_by('-submitted_at')
        )
        feedbacks = [
            {
                'rating': fb.rating,
                'comment': fb.comment,
                'user_name': fb.user.get_full_name() or fb.user.username,
                'submitted_at': fb.submitted_at.strftime('%Y-%m-%d %H:%M'),
            }
            for fb in feedbacks_qs
        ]

        return JsonResponse({
            'title': event.title,
            'club_name': event.club.name,
            'start_time': event.start_time.strftime('%Y-%m-%d %I:%M %p'),
            'location': event.location,
            'description': event.description,
            'feedbacks': feedbacks,
            'can_give_feedback': can_give_feedback,
        })

    existing_feedback = EventFeedback.objects.filter(event=event, user=request.user).first()
    media = EventMedia.objects.filter(event=event).order_by('media_type', '-uploaded_at')

    return render(request, 'users/past_event_details.html', {
        'event': event,
        'registration': registration,
        'existing_feedback': existing_feedback,
        'media': media,
    })
