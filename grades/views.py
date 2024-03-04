from django.shortcuts import render, redirect
from . import models
from django.http import Http404, HttpResponseBadRequest, HttpResponse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count
from django.core.exceptions import PermissionDenied

# ASSIGNMENTS PAGE -----
@login_required
def assignments(request):
    # Get ALL assignments
    assignments = models.Assignment.objects.all()

    return render(request, "assignments.html", {"assignments": assignments})

# INDEX PAGE (specific assignment) -----
@login_required
def index(request, assignment_id):
    # Make sure the request is valid
    try:
        assignment = models.Assignment.objects.get(id=assignment_id)
    except models.Assignment.DoesNotExist:
        raise Http404("Assignment ID is invalid.")
    
    # Total submissions for the assignment
    totalSubs = models.Submission.objects.filter(assignment__id=assignment_id).count()

    # Of those submissions, the ones that are assigned to ta1
    assignedSubs = models.Submission.objects.filter(grader__username=request.user.username, assignment__id=assignment_id).count()

    # The number of students
    totalStudents = models.Group.objects.get(name="Students").user_set.count()

    submission = models.Submission.objects.filter(assignment=assignment, author__username=request.user.username)
    current_datetime = timezone.now()
    student_message = None

    if is_student(request.user):
        # calculate score if able
        if(submission.count() > 0 and submission.first().score is not None):
            score = submission.first().score / assignment.points * 100
            formatted_score = "{:.1f}%".format(score)
            student_message = f"Your submission, {submission.first().file.name}, received {submission.first().score}/{assignment.points} points ({formatted_score})"

        # check if the submissions hasn't been graded yet
        elif(submission.count() > 0 and submission.first().score is None):
            if assignment.deadline > current_datetime:
                student_message = f"Your current submission is {submission.first().file.name}"
            else:
                student_message = f"Your submission, {submission.first().file.name}, is being graded"

        # nothing has been submitted
        else:
            if assignment.deadline > current_datetime:
                student_message = "No current submission"
            else:
                student_message = "You did not submit this assignment and received 0 points"

    return render(request, "index.html", {"assignment": assignment, "totalSubs": totalSubs, "assignedSubs": assignedSubs, "totalStudents": totalStudents, "is_ta": is_ta(request.user) or is_admin(request.user), "student_message": student_message, "notdue": assignment.deadline > current_datetime})

# Helper function to return whether or not a user is a TA
def is_ta(user):
    return user.groups.filter(name="Teaching Assistants").exists()

# Helper function to return whether or not a user is a TA
def is_student(user):
    return user.groups.filter(name="Students").exists()

# Helper function to return whether or not a user is an Admin
def is_admin(user):
    return user.is_superuser

def ta_or_admin(user):
    return is_ta(user) or is_admin(user)

# SUBMISSIONS PAGE (specific assignment) -----
@login_required
@user_passes_test(ta_or_admin)
def submissions(request, assignment_id):
    # All of the submissions for the specified assignment that the user needs to grade (sorted alphabetically by student username)
    submissions = None
    if is_admin(request.user):
        submissions = models.Submission.objects.filter(assignment__id=assignment_id).order_by('author__username')
    elif is_ta(request.user):
        submissions = models.Submission.objects.filter(assignment__id=assignment_id, grader__username=request.user.username).order_by('author__username')

    # Get the respective assignment
    assignment = models.Assignment.objects.get(id=assignment_id)

    return render(request, "submissions.html", {"submissions": submissions, "assignment": assignment})

# PROFILE PAGE -----
@login_required
def profile(request):
    # Get all assignments
    assignments = models.Assignment.objects.all()

    # Create a dictionary that maps assignment to the grade status
    assignment_data = {}
    current_datetime = timezone.now()

    # TAs or Admin
    if(is_admin(request.user) or is_ta(request.user)):
        for assignment in assignments:
            # check if the assignment isn't due yet
            if(assignment.deadline > current_datetime):
                assignment_data[assignment] = "Not due"
            else:
                # The number of submissions user has graded
                graded_count = None
                if(is_admin(request.user)):
                    graded_count = models.Submission.objects.filter(assignment=assignment, score__isnull=False).count()
                else:
                    graded_count = models.Submission.objects.filter(assignment=assignment, grader__username=request.user.username, score__isnull=False).count()

                # The number of submissions assigned to user
                assigned_count = None
                if(is_admin(request.user)):
                    assigned_count =  models.Submission.objects.filter(assignment=assignment).count()
                else:
                    assigned_count =  models.Submission.objects.filter(assignment=assignment, grader__username=request.user.username).count()

                # Create a string from the values
                assignment_data[assignment] = f"{graded_count}/{assigned_count}"
    
    # Students
    points_available = 0
    points_earned = 0
    formatted_grade = None
    if(is_student(request.user)):
        for assignment in assignments:
            submission = models.Submission.objects.filter(assignment=assignment, author__username=request.user.username)

            # calculate score if able
            if(submission.count() > 0 and submission.first().score is not None):
                score = submission.first().score / assignment.points * 100
                formatted_score = "{:.1f}%".format(score)
                assignment_data[assignment] = formatted_score
                points_available += assignment.weight
                points_earned += assignment.weight * submission.first().score / assignment.points

            # check if the submissions hasn't been graded yet
            elif(submission.count() > 0 and submission.first().score is None):
                assignment_data[assignment] = "Ungraded"

            # nothing has been submitted
            else:
                if assignment.deadline > current_datetime:
                    assignment_data[assignment] = "Not due"
                else:
                    assignment_data[assignment] = "Missing"
                    points_available += assignment.weight

        grade = points_earned / points_available * 100
        formatted_grade = "{:.1f}%".format(grade)

    return render(request, "profile.html", {"assignment_data": assignment_data, "user": request.user, "grade": formatted_grade})

# LOGIN PAGE -----
def login_form(request):
    if request.method == "GET":
        next = request.GET.get("next", "/profile")
        return render(request, "login.html", {"next": next})

    elif request.method == 'POST':
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        next = request.POST.get("next", "/profile")
        if user is not None:
            login(request, user)
            return redirect(next)
        else:
            return render(request, "login.html", {"next": next, "error": "Username and password do not match."})

def logout_form(request):
    logout(request)
    return redirect(f"/profile/login")

# GRADE FORM -----
@require_POST
@login_required
@user_passes_test(ta_or_admin)
def grade(request, assignment_id):
    for key in request.POST:
        if key.startswith("grade"):
            # Grab the submission ID
            submission_id = int(key[6:])

            # Make sure the submission ID is valid
            try:
                submission = models.Submission.objects.get(id=submission_id)
            except models.Submission.DoesNotExist:
                raise HttpResponseBadRequest("Submission ID is invalid.")
            
            # Make sure the score is a float
            try:
                grade = float(request.POST[key])
                submission.score = grade
            except ValueError:
                submission.score = None

            submission.save()
            
    return redirect(f"/{assignment_id}/submissions")

# SUBMIT FILE -----
@require_POST
@login_required
@user_passes_test(is_student)
def submit(request, assignment_id):
    # Make sure the request is valid
    try:
        assignment = models.Assignment.objects.get(id=assignment_id)
    except models.Assignment.DoesNotExist:
        raise Http404("Assignment ID is invalid.")
    
    current_datetime = timezone.now()
    if assignment.deadline < current_datetime:
        raise HttpResponseBadRequest("Assignment is past due.")
    
    file = request.FILES.get("submittedFile", None)
    if(file is None):
        return

    submissions = models.Submission.objects.filter(assignment=assignment, author__username=request.user.username)
    submission = models.Submission.objects.filter(assignment=assignment, author__username=request.user.username).first()

    if submissions.count() > 0:
        submission.file = file
        submission.save()
    else:
        new_submission = models.Submission.objects.create(
            assignment = assignment,
            author = request.user,
            grader = pick_grader(assignment),
            file = file,
            score = None
        )
        new_submission.save()

    return redirect(f"/{assignment_id}/")

def pick_grader(assignment):
    return models.Group.objects.get(name="Teaching Assistants").user_set.annotate(total_assigned = Count("graded_set")).order_by("total_assigned").first()
    
def show_upload(request, filename):
    submission = models.Submission.objects.filter(file=filename).first()
    if not (request.user == submission.author or request.user == submission.grader or is_admin(request.user)):
        raise PermissionDenied("Permission denied.")
    with submission.file.open() as fd:
        response = HttpResponse(fd)
        response["Content-Disposition"] = \
            f'attachment; filename="{submission.file.name}"'
        return response
