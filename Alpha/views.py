from django.shortcuts import render,HttpResponse,redirect,get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login,logout as auth_logout
from Alpha.models import Contact
from admin_portal.models import Event, Payment, PlanPayment
from datetime import date
import razorpay, weasyprint
from django.http import JsonResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from django.views.decorators.csrf import csrf_exempt
import json
from django.core.mail import send_mail, EmailMessage
from django.contrib.auth.decorators import login_required
from django.conf import settings 

# Create your views here.
def register(request):
    if request.method == 'GET':
        return render(request, 'register.html')
    
    fname = request.POST['fname'].strip()
    lname = request.POST['lname'].strip()
    username = request.POST['uname'].strip()
    email = request.POST['uemail'].strip()
    password = request.POST['upass']
    confirm_password = request.POST['ucpass']

    context = {}

    if not fname.isalpha():
        context['errmsg'] = "First name can only have letters"
        return render(request, 'register.html', context)
    
    if not lname.isalpha():
        context['errmsg'] = "Last name can only have letters"
        return render(request, 'register.html', context)

    if len(password) < 8:
        context['errmsg'] = "Password must be at least 8 characters"
        return render(request, 'register.html', context)

    special_chars = "!@#$%^&*()_-+=[]{}|;:\"<>,./?'"
    if not any(char in special_chars for char in password):
        context['errmsg'] = "Password must contain at least 1 special character"
        return render(request, 'register.html', context)

    if password != confirm_password:
        context['errmsg'] = "Passwords do not match"
        return render(request, 'register.html', context)

    try:
        user = User.objects.create(
            username=username,
            email=email,
            first_name=fname,
            last_name=lname
        )
        user.set_password(password)
        user.save()
        return redirect('/login')
    except:
        context['errmsg'] = "Username already exists!"
        return render(request, 'register.html', context)


def user_login(request):
    if request.method=='GET':
        return render(request, 'login.html') 
    else:
        name=request.POST['uname']
        p=request.POST['upass']

        #print(name)
        #print(p)

        u=authenticate(username=name,password=p)
        #print(u)
        if u is not None: 
            #print('Login Successfull!!')
            login(request,u)
            #return HttpResponse('Login Successfull!!')
            return redirect('/home') 

        else:
            #print('Invalid Credentials..')
            context={}
            context['errmsg']='Invalid Credentials'
            return render(request,'login.html',context)


def logout(request):
    auth_logout(request)
    return redirect('/home')


def home(request) :
    upcoming_events = Event.objects.filter(status="upcoming").order_by("date")[:3]
    return render(request, "homepage.html", {"upcoming_events": upcoming_events})


def events(request):
    filter_type = request.GET.get("filter", "upcoming")
    events = Event.objects.filter(status=filter_type).order_by("date")
    print("Filter:", filter_type, "| Found events:", events.count())
    return render(request, "events.html", {
        "events": events,
        "filter_type": filter_type
    })


def event_detail(request, id):
    event = get_object_or_404(Event, id=id)

    if request.method == 'POST':
        Registration.objects.create(user=request.user, event=event)
        return redirect('event_success', event_id=event.id)

    return render(request, "event_detail.html", {"event": event})


@login_required(login_url='/login')
def start_payment(request, id):
    event = get_object_or_404(Event, id=id)

    client = razorpay.Client(auth=("rzp_test_RDfG0Blcon2Nrc", "SvaxlHa43D5C4oMeq3F2gDb6"))

    order_data = {
        "amount": int(event.price * 100),  
        "currency": "INR",
        "payment_capture": 1
    }
    order = client.order.create(order_data)

    return render(request, "Events_Payment.html", {
        "event": event,
        "order": order,
        "razorpay_key": "rzp_test_RDfG0Blcon2Nrc",
    })


@login_required(login_url='/login')
def payment_call(request, id):
    event = get_object_or_404(Event, id=id)

    if request.method == "POST":
        data = json.loads(request.body)
        quantity = int(data.get("quantity", 1))
        razorpay_payment_id = data.get("razorpay_payment_id")

        Payment.objects.create(
            user=request.user,
            event=event,
            amount=event.price,  
            quantity=quantity,
            status="SUCCESS"
        )

        return JsonResponse({"success": True})


@login_required(login_url='/login')
def event_success(request):
    """
    Render the success page and send a confirmation email
    after a successful event registration/payment.
    Assumes that the last Payment made by the user corresponds to the event.
    """
    try:
        last_payment = Payment.objects.filter(user=request.user).latest('id')
        event = last_payment.event 
        quantity = last_payment.quantity

        subject = f"Thank You for Registering for {event.title}!"
        message = f"""
Hi {request.user.get_full_name() or request.user.username},

Thank you for registering for {event.title} at Alpha Run Club! 🎉

Event Details:
- Date: {event.date.strftime('%A, %d %B %Y')}
- Time: {event.start_time.strftime('%I:%M %p')} to {event.end_time.strftime('%I:%M %p') if event.end_time else 'N/A'}
- Venue: {event.location}
- Number of Tickets: {quantity}

We’re excited to see you there! Arrive 15 minutes early and stay hydrated.

If you have any questions, contact us at {event.contact_email or settings.EMAIL_HOST_USER}.

See you soon,
Alpha Run Club Team
"""

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[request.user.email],
            fail_silently=False
        )

    except Payment.DoesNotExist:
        event = None
        quantity = None

    return render(request, 'event_success.html', {'event': event, 'quantity': quantity})


def billing_history(request):
    search_query = request.GET.get('search', '')
    type_filter = request.GET.get('type', 'All')

    event_payments = Payment.objects.filter(user=request.user).select_related('event')
    plan_payments = PlanPayment.objects.filter(user=request.user)

    all_payments = list(event_payments) + list(plan_payments)

    if type_filter in ['Event', 'Plan']:
        if type_filter == 'Event':
            all_payments = [p for p in all_payments if hasattr(p, 'event')]
        else:
            all_payments = [p for p in all_payments if hasattr(p, 'plan_type')]

    if search_query:
        all_payments = [
            p for p in all_payments
            if (hasattr(p, 'event') and search_query.lower() in p.event.title.lower())
            or (hasattr(p, 'plan_type') and search_query.lower() in p.plan_type.lower())
        ]

    all_payments = sorted(all_payments, key=lambda x: x.created_at, reverse=True)

    return render(request, 'billing_history.html', {'payments': all_payments})


def download_receipt(request, id):
    payment = get_object_or_404(Payment, id=id, user=request.user)

    html_string = render_to_string('Receipt.html', {'payment': payment})

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Receipt_{payment.id}.pdf"'

    weasyprint.HTML(string=html_string).write_pdf(response)

    return response


def download_plan_receipt(request, id):
    payment = get_object_or_404(PlanPayment, id=id, user=request.user)
    
    html_string = render_to_string('plan_receipt.html', {'payment': payment})
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="PlanReceipt_{payment.id}.pdf"'
    
    weasyprint.HTML(string=html_string).write_pdf(response)
    
    return response


def contact(request):
    if request.method=='GET': 
        return render(request, 'contact.html')
    else: 
        n=request.POST['cname']
        mail=request.POST['cmail']
        mob=request.POST['cmob']
        msg=request.POST['cmsg']

        #print(n)
        #print(mail)
        #print(mob)
        #print(msg)

        c=Contact.objects.create(name=n, email=mail, mobile=mob, message=msg)
        context={}
        return render(request,'thankyou.html',context)


def thankyou(request):
    return render(request, 'thankyou.html')

def runtrack(request):
    return render(request, 'livetracker.html')


def apd(request):
    return render(request,'apd.html')


def plans(request):
    return render(request,'plans.html')


@login_required(login_url='/login')
def payment(request, type):
    client = razorpay.Client(auth=("rzp_test_RDfG0Blcon2Nrc", "SvaxlHa43D5C4oMeq3F2gDb6"))

    plan_prices = {
        "monthly": 2500,
        "quarterly": 6000,
        "half-yearly": 10000,
    } 

    amount = plan_prices.get(type, 2500)
    razorpay_amount = int(amount * 100)

    payment_order = client.order.create({
        "amount": razorpay_amount,
        "currency": "INR",
        "payment_capture": "1"
    })

    request.session['plan_type'] = type
    request.session['amount'] = amount

    context = {
        "razorpay_key": "rzp_test_RDfG0Blcon2Nrc",
        "order_id": payment_order.get("id"),  
        "amount": amount,
        "plan_type": type,
    }

    return render(request, "payments.html", context)


@login_required(login_url='/login')
def paymentsuccess(request):
    """
    Handles the plan payment success page:
    - Saves payment in the database (avoids duplicates)
    - Sends a confirmation email to the user
    """

    plan_type = request.session.get('plan_type')
    amount = request.session.get('amount')
    payment_id = request.session.get('payment_id')
    order_id = request.session.get('order_id')
    status = request.session.get('status', 'SUCCESS')  

    if plan_type and amount and payment_id and order_id:
        payment_exists = PlanPayment.objects.filter(
            user=request.user,
            plan_type=plan_type,
            razorpay_order_id=order_id
        ).exists()

        if not payment_exists:
            PlanPayment.objects.create(
                user=request.user,
                plan_type=plan_type,
                amount=amount,
                status=status,
                razorpay_order_id=order_id,
                payment_id=payment_id
            )

            subject = "Payment Successful - Alpha Run Club"
            message = f"""
Hi {request.user.get_full_name() or request.user.username},

Your payment for the {plan_type} plan has been successfully received.

Amount Paid: ₹{amount}
Payment ID: {payment_id}
Order ID: {order_id}

Thank you for joining Alpha Run Club! We’re excited to have you on board.

Best regards,
Alpha Run Club Team
"""
            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,
                [request.user.email],
                fail_silently=False
            )

    for key in ['plan_type', 'amount', 'payment_id', 'order_id', 'status']:
        if key in request.session:
            del request.session[key]

    return render(request, 'success.html')


@csrf_exempt
def save_plan_payment(request):
    if request.method == "POST":
        data = json.loads(request.body)
        plan_type = data.get("plan_type")
        amount = data.get("amount")
        razorpay_order_id = data.get("razorpay_order_id")
        razorpay_payment_id = data.get("payment_id")

        request.session['plan_type'] = plan_type
        request.session['amount'] = amount
        request.session['order_id'] = razorpay_order_id
        request.session['payment_id'] = razorpay_payment_id
        request.session['status'] = "SUCCESS"

        return JsonResponse({"success": True})


def coaches(request):
    return render(request,'coaches.html')


def bmi_tracker(request):
    return render(request, "bmi_tracker.html")