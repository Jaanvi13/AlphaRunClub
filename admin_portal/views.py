from django.shortcuts import render,HttpResponse,redirect,get_object_or_404
from .forms import EventForm
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.db.models import Q
from .models import Event, Payment, PlanPayment, User
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from decimal import Decimal


@login_required(login_url='/admin/login/')
def admin_login(request):

    if request.method == 'GET':
        return render(request, 'Alogin.html') 

    username = request.POST.get('uname').strip()
    password = request.POST.get('upass').strip()

    user = authenticate(request, username=username, password=password)

    if user:  
        if user.is_staff or user.is_superuser:
            login(request, user)  
            return redirect('/admin')  
        else:
            return render(request, 'Alogin.html', {
                'errmsg': 'You are not authorized to access the admin portal.'
            })
    else:
        return render(request, 'Alogin.html', {
            'errmsg': 'Invalid username or password.'
        })


@login_required(login_url='/admin/login/')
def user_admin(request): 
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):

        total_users = User.objects.count()
        total_events = Event.objects.count()
        total_event_payments = Payment.objects.count()
        total_plan_payments = PlanPayment.objects.count()

        total_event_revenue = Payment.objects.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        total_plan_revenue = PlanPayment.objects.aggregate(total=Sum('amount'))['total'] or 0.0
        total_plan_revenue = Decimal(str(total_plan_revenue))
        total_revenue = total_event_revenue + total_plan_revenue

        payment_status_data = Payment.objects.values('status').annotate(count=Count('id'))
        plan_status_data = PlanPayment.objects.values('status').annotate(count=Count('id'))

        context = {
            'total_users': total_users,
            'total_events': total_events,
            'total_event_payments': total_event_payments,
            'total_plan_payments': total_plan_payments,
            'total_revenue': total_revenue,
            'payment_status_data': list(payment_status_data),
            'plan_status_data': list(plan_status_data),
        }

        return render(request, 'admindashboard.html', context)

    else:
        messages.error(request, "You must log in as staff to access this page.")
        return redirect('/admin/login/')


def admin_logout(request):
    logout(request)
    return redirect('/admin/login')


@login_required(login_url='/admin/login/')
def create_event(request):
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('create_event') 
    else:
        form = EventForm()
    return render(request, 'eventmanagement.html', {'form': form})


@login_required(login_url='/admin/login/')
def eventlist(request):
    events = Event.objects.all().order_by('-date')
    return render(request, 'eventlist.html', {'events': events})


@login_required(login_url='/admin/login/')
def eventedit(request, id):
    event = get_object_or_404(Event, id=id)
    if request.method == "POST":
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            return redirect("eventlist") 
    else:
        form = EventForm(instance=event)
    return render(request, "eventedit.html", {"form": form, "event": event})


@login_required(login_url='/admin/login/')
def eventdelete(request, id):
    event = get_object_or_404(Event, id=id)
    if request.method == "POST":
        event.delete()
        return redirect("events") 
    return redirect("eventedit", id=id)


@login_required(login_url='/admin/login/')
def user_management(request):
    search_query = request.GET.get('search', '').strip()
    role_filter = request.GET.get('role', 'All')
    status_filter = request.GET.get('status', 'All')
    date_filter = request.GET.get('date_joined', '')

    users = User.objects.all()

    if search_query:
        users = users.filter(Q(username__icontains=search_query) | Q(email__icontains=search_query))

    if role_filter != "All":
        if role_filter == "Admin":
            users = users.filter(is_staff=True, is_superuser=True)
        elif role_filter == "Staff":
            users = users.filter(is_staff=True, is_superuser=False)
        elif role_filter == "User":
            users = users.filter(is_staff=False, is_superuser=False)

    if status_filter != "All":
        if status_filter == "Active":
            users = users.filter(is_active=True)
        elif status_filter == "Inactive":
            users = users.filter(is_active=False)

    if date_filter:
        users = users.filter(date_joined=date_filter)

    context = {
        'users': users,  
    }
    return render(request, 'usermanagement.html', context)


@login_required(login_url='/admin/login/')
def user_edit(request, eid):
    user = get_object_or_404(User, id=eid)

    if request.method == "POST":
        user.username = request.POST.get("username")
        user.email = request.POST.get("email")
        user.first_name = request.POST.get("first_name")
        user.last_name = request.POST.get("last_name")

        status = request.POST.get("status")
        user.is_active = True if status == "Active" else False
        
        role = request.POST.get("role")
        if role == "Admin":
            user.is_staff = True
            user.is_superuser = True
        elif role == "Staff":
            user.is_staff = True
            user.is_superuser = False
        else:  
            user.is_staff = False
            user.is_superuser = False

        user.save() 
        return redirect('user_management')

    if request.method == 'GET':    
        return render(request, "useredit.html", {"user": user})
    

@login_required(login_url='/admin/login/')
def user_delete(request, eid):
    user = get_object_or_404(User, id=eid)

    if request.method == "POST":
        user.delete()
        return redirect('user_management')

    return redirect('user_management')


@login_required(login_url='/admin/login/')
def user_add(request): 
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        password = request.POST.get("password")
        role = request.POST.get("role")
        status = request.POST.get("status")

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        if role == "Admin":
            user.is_staff = True
            user.is_superuser = True
        elif role == "Staff":
            user.is_staff = True
            user.is_superuser = False
        else:  
            user.is_staff = False
            user.is_superuser = False

        user.is_active = True if status == "Active" else False

        user.save()
        return redirect('user_management')

    return redirect('user_management')


@login_required(login_url='/admin/login/')
def event_payments(request):
    payments = Payment.objects.select_related('user', 'event').all().order_by('-created_at')

    total_event_payments = payments.count()

    total_revenue = payments.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    context = {
        'payments': payments,
        'total_event_payments': total_event_payments,
        'total_revenue': total_revenue,
    }
    return render(request, "event_payments.html", context)


@login_required(login_url='/admin/login/')
def plan_payments(request):
    plan_payments = PlanPayment.objects.select_related('user').all().order_by('-created_at')

    total_plan_payments = plan_payments.count()
    total_revenue = plan_payments.aggregate(total=Sum('amount'))['total'] or 0.0
    total_revenue = Decimal(str(total_revenue))

    context = {
        'plan_payments': plan_payments,
        'total_plan_payments': total_plan_payments,
        'total_revenue': total_revenue,
    }

    return render(request, 'plan_payments.html', context)