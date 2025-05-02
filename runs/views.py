from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Sum, F, FloatField, ExpressionWrapper
from django.db.models.functions import TruncMonth, TruncYear
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import connection, transaction
from .models import Runner, Route, Run, Comment, RunLike
from .forms import RunForm, RouteForm, CommentForm, RunFilterForm
from datetime import timedelta
from decimal import Decimal
import json
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate

# Run CRUD Operations (Requirement 1)
@transaction.atomic
@login_required
def run_list(request):
    """List all runs for the logged-in user using prepared statement."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT r.id, r.title, r.date, r.start_time, r.duration, r.distance_km, 
                       r.average_pace, r.calories_burned, r.weather_conditions, r.is_public
                FROM runs_run r
                JOIN runs_runner rr ON r.runner_id = rr.id
                WHERE rr.user_id = %s
                ORDER BY r.date DESC, r.start_time DESC
            """, [request.user.id])
            
            columns = [col[0] for col in cursor.description]
            runs = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            # Convert duration and average_pace to timedelta objects
            for run in runs:
                if run['duration']:
                    run['duration'] = timedelta(seconds=run['duration'].total_seconds())
                if run['average_pace']:
                    run['average_pace'] = timedelta(seconds=run['average_pace'].total_seconds())
            
            return render(request, 'runs/run_list.html', {'runs': runs})
    except Runner.DoesNotExist:
        messages.error(request, "You need to create a runner profile first.")
        return redirect('runs:create_runner')

@transaction.atomic
@login_required
def run_detail(request, pk):
    """Get run details using prepared statement."""
    try:
        current_runner = Runner.objects.get(user=request.user)
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT r.*, rr.user_id, rt.name as route_name, u.username as runner_username
                FROM runs_run r
                JOIN runs_runner rr ON r.runner_id = rr.id
                JOIN auth_user u ON rr.user_id = u.id
                LEFT JOIN runs_route rt ON r.route_id = rt.id
                WHERE r.id = %s AND (r.is_public = true OR r.runner_id = %s)
            """, [pk, current_runner.id])
            
            columns = [col[0] for col in cursor.description]
            run_data = cursor.fetchone()
            
            if not run_data:
                raise Run.DoesNotExist
                
            run = dict(zip(columns, run_data))
            
            # Convert duration and average_pace to timedelta objects
            if run['duration']:
                run['duration'] = timedelta(seconds=run['duration'].total_seconds())
            if run['average_pace']:
                run['average_pace'] = timedelta(seconds=run['average_pace'].total_seconds())
            
            # Get comments using ORM (simple operation)
            comments = Comment.objects.filter(run_id=pk).select_related('commenter')
            
            # Process comment form if submitted
            if request.method == 'POST':
                comment_form = CommentForm(request.POST)
                if comment_form.is_valid():
                    # Check for spam/duplicate comments
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            SELECT COUNT(*) 
                            FROM runs_comment 
                            WHERE run_id = %s AND commenter_id = %s 
                            AND content = %s 
                            AND created_at > NOW() - INTERVAL '5 minutes'
                        """, [pk, current_runner.id, comment_form.cleaned_data['content']])
                        
                        if cursor.fetchone()[0] > 0:
                            messages.error(request, "You've already posted this comment recently.")
                        else:
                            comment = comment_form.save(commit=False)
                            comment.run_id = pk
                            comment.commenter = current_runner
                            comment.save()
                            messages.success(request, "Comment added successfully!")
                            return redirect('runs:run_detail', pk=pk)
            else:
                comment_form = CommentForm()
            
            return render(request, 'runs/run_detail.html', {
                'run': run,
                'comments': comments,
                'comment_form': comment_form,
                'is_owner': run['runner_id'] == current_runner.id
            })
    except Run.DoesNotExist:
        messages.error(request, "Run not found or you don't have permission to view it.")
        return redirect('runs:run_list')

@transaction.atomic
@login_required
def create_run(request):
    """Create a new run using ORM (simple operation)."""
    try:
        runner = Runner.objects.get(user=request.user)
    except Runner.DoesNotExist:
        messages.error(request, "You need to create a runner profile first.")
        return redirect('runs:create_runner')
        
    if request.method == 'POST':
        form = RunForm(request.POST)
        if form.is_valid():
            run = form.save(commit=False)
            run.runner = runner
            # Explicitly set is_public from the form data
            run.is_public = form.cleaned_data['is_public']
            run.save()
            messages.success(request, f"Run created successfully! Public: {run.is_public}")
            return redirect('runs:run_detail', pk=run.pk)
    else:
        initial_data = {}
        route_id = request.GET.get('route')
        if route_id:
            try:
                route = Route.objects.get(id=route_id, creator=runner)
                initial_data['route'] = route
                initial_data['distance_km'] = route.distance_km
            except Route.DoesNotExist:
                pass
                
        form = RunForm(initial=initial_data)
        
    # Get routes created by this user to populate the dropdown
    routes = Route.objects.filter(creator=runner)
    form.fields['route'].queryset = routes
        
    return render(request, 'runs/run_form.html', {
        'form': form,
        'title': 'Add New Run'
    })

@transaction.atomic
@login_required
def update_run(request, pk):
    """Update a run using ORM (simple operation)."""
    try:
        runner = Runner.objects.get(user=request.user)
        run = Run.objects.get(pk=pk, runner=runner)
    except (Runner.DoesNotExist, Run.DoesNotExist):
        messages.error(request, "Run not found.")
        return redirect('runs:run_list')
        
    if request.method == 'POST':
        form = RunForm(request.POST, instance=run)
        if form.is_valid():
            run = form.save(commit=False)
            # Explicitly set is_public from the form data
            run.is_public = form.cleaned_data['is_public']
            run.save()
            messages.success(request, f"Run updated successfully! Public: {run.is_public}")
            return redirect('runs:run_detail', pk=run.pk)
    else:
        form = RunForm(instance=run)
        
    return render(request, 'runs/run_form.html', {
        'form': form,
        'title': 'Edit Run'
    })

@transaction.atomic
@login_required
def delete_run(request, pk):
    """Delete a run using ORM (simple operation)."""
    try:
        runner = Runner.objects.get(user=request.user)
        run = Run.objects.get(pk=pk, runner=runner)
    except (Runner.DoesNotExist, Run.DoesNotExist):
        messages.error(request, "Run not found.")
        return redirect('runs:run_list')
        
    if request.method == 'POST':
        run.delete()
        messages.success(request, "Run deleted successfully!")
        return redirect('runs:run_list')
        
    return render(request, 'runs/run_confirm_delete.html', {'run': run})

# Route CRUD operations
@login_required
def route_list(request):
    """List all routes for the logged-in user."""
    try:
        runner = Runner.objects.get(user=request.user)
        routes = Route.objects.filter(creator=runner).order_by('name')
        return render(request, 'runs/route_list.html', {'routes': routes})
    except Runner.DoesNotExist:
        messages.error(request, "You need to create a runner profile first.")
        return redirect('runs:create_runner')

@transaction.atomic
@login_required
def create_route(request):
    """Create a new route with transaction for concurrent route creation."""
    try:
        runner = Runner.objects.get(user=request.user)
    except Runner.DoesNotExist:
        messages.error(request, "You need to create a runner profile first.")
        return redirect('runs:create_runner')
        
    if request.method == 'POST':
        form = RouteForm(request.POST)
        if form.is_valid():
            route = form.save(commit=False)
            route.creator = runner
            
            # Check for duplicate route names for this user
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM runs_route 
                    WHERE creator_id = %s AND LOWER(name) = LOWER(%s)
                """, [runner.id, route.name])
                
                if cursor.fetchone()[0] > 0:
                    messages.error(request, "A route with this name already exists.")
                    return render(request, 'runs/route_form.html', {
                        'form': form,
                        'title': 'Add New Route'
                    })
            
            route.save()
            messages.success(request, "Route created successfully!")
            return redirect('runs:route_list')
    else:
        form = RouteForm()
        
    return render(request, 'runs/route_form.html', {
        'form': form,
        'title': 'Add New Route'
    })

# Report Interface (Requirement 2)
@transaction.atomic
@login_required
def run_report(request):
    """Generate reports and statistics about runs using prepared statements."""
    try:
        runner = Runner.objects.get(user=request.user)
    except Runner.DoesNotExist:
        messages.error(request, "You need to create a runner profile first.")
        return redirect('runs:create_runner')
        
    form = RunFilterForm(request.GET or None)
    runs = Run.objects.filter(runner=runner)
    
    if form.is_valid():
        if form.cleaned_data.get('start_date'):
            runs = runs.filter(date__gte=form.cleaned_data['start_date'])
        if form.cleaned_data.get('end_date'):
            runs = runs.filter(date__lte=form.cleaned_data['end_date'])
        if form.cleaned_data.get('min_distance'):
            runs = runs.filter(distance_km__gte=form.cleaned_data['min_distance'])
        if form.cleaned_data.get('max_distance'):
            runs = runs.filter(distance_km__lte=form.cleaned_data['max_distance'])
        if form.cleaned_data.get('route'):
            runs = runs.filter(route=form.cleaned_data['route'])
    
    stats = {}
    if runs.exists():
        # Use prepared statements for complex statistics
        with connection.cursor() as cursor:
            # Get basic statistics from filtered runs
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_runs,
                    SUM(distance_km) as total_distance,
                    AVG(distance_km) as avg_distance,
                    AVG(EXTRACT(EPOCH FROM duration)) as avg_duration_seconds
                FROM runs_run
                WHERE id IN %s
            """, [tuple(runs.values_list('id', flat=True))])
            
            row = cursor.fetchone()
            stats['total_runs'] = row[0]
            stats['total_distance'] = float(row[1]) if row[1] else 0
            stats['avg_distance'] = float(row[2]) if row[2] else 0
            stats['avg_duration_minutes'] = round(float(row[3]) / 60, 2) if row[3] else 0
            
            # Get monthly statistics from filtered runs
            cursor.execute("""
                SELECT 
                    EXTRACT(YEAR FROM date) as year,
                    EXTRACT(MONTH FROM date) as month,
                    COUNT(*) as run_count,
                    SUM(distance_km) as total_distance,
                    AVG(distance_km) as avg_distance
                FROM runs_run
                WHERE id IN %s
                GROUP BY year, month
                ORDER BY year DESC, month DESC
                LIMIT 12
            """, [tuple(runs.values_list('id', flat=True))])
            
            monthly_stats = []
            for row in cursor.fetchall():
                monthly_stats.append({
                    'year': int(row[0]),
                    'month': int(row[1]),
                    'run_count': int(row[2]),
                    'total_distance': float(row[3]),
                    'avg_distance': float(row[4])
                })
            
            stats['monthly_stats'] = json.dumps(monthly_stats)
            
            # Get route statistics from filtered runs
            cursor.execute("""
                SELECT 
                    r.name,
                    COUNT(*) as run_count,
                    AVG(ru.distance_km) as avg_distance,
                    AVG(EXTRACT(EPOCH FROM ru.duration)) as avg_duration_seconds
                FROM runs_route r
                JOIN runs_run ru ON r.id = ru.route_id
                WHERE ru.id IN %s
                GROUP BY r.id, r.name
                ORDER BY run_count DESC
            """, [tuple(runs.values_list('id', flat=True))])
            
            route_stats = []
            for row in cursor.fetchall():
                route_stats.append({
                    'name': row[0],
                    'run_count': int(row[1]),
                    'avg_distance': float(row[2]),
                    'avg_duration_minutes': round(float(row[3]) / 60, 2) if row[3] else 0
                })
            
            stats['route_stats'] = route_stats
    
    return render(request, 'runs/run_report.html', {
        'form': form,
        'runs': runs,
        'stats': stats
    })

# Runner profile creation
@login_required
def create_runner(request):
    """Create a runner profile for a logged-in user."""
    # Check if the user already has a runner profile
    if Runner.objects.filter(user=request.user).exists():
        messages.info(request, "You already have a runner profile.")
        return redirect('runs:run_list')
        
    if request.method == 'POST':
        # Simple form processing for runner profile
        bio = request.POST.get('bio', '')
        age = request.POST.get('age')
        height_cm = request.POST.get('height_cm')
        weight_kg = request.POST.get('weight_kg')
        
        # Create the runner profile
        runner = Runner(
            user=request.user,
            bio=bio,
        )
        
        if age:
            runner.age = int(age)
        if height_cm:
            runner.height_cm = int(height_cm)
        if weight_kg:
            runner.weight_kg = Decimal(weight_kg)
            
        runner.save()
        
        messages.success(request, "Runner profile created successfully!")
        return redirect('runs:run_list')
        
    return render(request, 'runs/create_runner.html')

# User registration view
def register(request):
    """Register a new user."""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            messages.success(request, f"Account created for {username}!")
            return redirect('runs:create_runner')
    else:
        form = UserCreationForm()
    return render(request, 'runs/register.html', {'form': form})

@transaction.atomic
@login_required
def add_comment(request, run_id):
    """Add a comment to a run with transaction for concurrent commenting."""
    try:
        runner = Runner.objects.get(user=request.user)
        run = Run.objects.get(id=run_id)
    except (Runner.DoesNotExist, Run.DoesNotExist):
        messages.error(request, "Invalid request.")
        return redirect('runs:run_list')
        
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            # Check for spam/duplicate comments
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM runs_comment 
                    WHERE run_id = %s AND commenter_id = %s 
                    AND content = %s 
                    AND created_at > NOW() - INTERVAL '5 minutes'
                """, [run_id, runner.id, form.cleaned_data['content']])
                
                if cursor.fetchone()[0] > 0:
                    messages.error(request, "You've already posted this comment recently.")
                    return redirect('runs:run_detail', pk=run_id)
            
            comment = form.save(commit=False)
            comment.run = run
            comment.commenter = runner
            comment.save()
            messages.success(request, "Comment added successfully!")
            
    return redirect('runs:run_detail', pk=run_id)

@transaction.atomic
@login_required
def toggle_like(request, run_id):
    """Toggle like on a run with transaction for concurrent likes."""
    try:
        runner = Runner.objects.get(user=request.user)
        run = Run.objects.get(id=run_id)
    except (Runner.DoesNotExist, Run.DoesNotExist):
        return JsonResponse({'error': 'Invalid request'}, status=400)
        
    # Use prepared statement to check and toggle like
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT EXISTS(
                SELECT 1 FROM runs_runlike 
                WHERE run_id = %s AND runner_id = %s
            )
        """, [run_id, runner.id])
        
        already_liked = cursor.fetchone()[0]
        
        if already_liked:
            cursor.execute("""
                DELETE FROM runs_runlike 
                WHERE run_id = %s AND runner_id = %s
            """, [run_id, runner.id])
            liked = False
        else:
            cursor.execute("""
                INSERT INTO runs_runlike (run_id, runner_id, created_at)
                VALUES (%s, %s, NOW())
            """, [run_id, runner.id])
            liked = True
            
        # Get updated like count
        cursor.execute("""
            SELECT COUNT(*) FROM runs_runlike WHERE run_id = %s
        """, [run_id])
        like_count = cursor.fetchone()[0]
        
    return JsonResponse({
        'liked': liked,
        'like_count': like_count
    })

@transaction.atomic
@login_required
def public_runs(request):
    """View public runs from other users."""
    try:
        current_runner = Runner.objects.get(user=request.user)
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT r.id, r.title, r.date, r.start_time, r.duration, r.distance_km, 
                       r.average_pace, r.calories_burned, r.weather_conditions,
                       rr.user_id, u.username as runner_username, r.is_public
                FROM runs_run r
                JOIN runs_runner rr ON r.runner_id = rr.id
                JOIN auth_user u ON rr.user_id = u.id
                WHERE r.is_public = true AND r.runner_id != %s
                ORDER BY r.date DESC, r.start_time DESC
            """, [current_runner.id])
            
            columns = [col[0] for col in cursor.description]
            runs = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            # Convert duration and average_pace to timedelta objects
            for run in runs:
                if run['duration']:
                    run['duration'] = timedelta(seconds=run['duration'].total_seconds())
                if run['average_pace']:
                    run['average_pace'] = timedelta(seconds=run['average_pace'].total_seconds())
            
            return render(request, 'runs/public_runs.html', {'runs': runs})
    except Runner.DoesNotExist:
        messages.error(request, "You need to create a runner profile first.")
        return redirect('runs:create_runner')

@transaction.atomic
@login_required
def view_user_runs(request, username):
    """View a specific user's public runs."""
    try:
        current_runner = Runner.objects.get(user=request.user)
        target_user = get_object_or_404(User, username=username)
        target_runner = Runner.objects.get(user=target_user)
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT r.id, r.title, r.date, r.start_time, r.duration, r.distance_km, 
                       r.average_pace, r.calories_burned, r.weather_conditions
                FROM runs_run r
                WHERE r.runner_id = %s AND (r.is_public = true OR r.runner_id = %s)
                ORDER BY r.date DESC, r.start_time DESC
            """, [target_runner.id, current_runner.id])
            
            columns = [col[0] for col in cursor.description]
            runs = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            # Convert duration and average_pace to timedelta objects
            for run in runs:
                if run['duration']:
                    run['duration'] = timedelta(seconds=run['duration'].total_seconds())
                if run['average_pace']:
                    run['average_pace'] = timedelta(seconds=run['average_pace'].total_seconds())
            
            return render(request, 'runs/user_runs.html', {
                'runs': runs,
                'target_user': target_user
            })
    except Runner.DoesNotExist:
        messages.error(request, "You need to create a runner profile first.")
        return redirect('runs:create_runner')
