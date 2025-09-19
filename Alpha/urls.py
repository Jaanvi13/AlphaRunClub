from django.urls import path, include, reverse_lazy
from Alpha import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('register',views.register),
    path('login',views.user_login),
    path('home',views.home),
    path('events',views.events, name='events'),
    path('events/<id>/', views.event_detail, name='event_detail'),
    path('events/<id>/pay/', views.start_payment, name="start_payment"),
    path('payment/<id>/',views.payment_call, name="payment_callback"),
    path('event-success/', views.event_success, name='event_success'),
    path('billing-history',views.billing_history, name="billing_history"),
    path('receipt/<id>/', views.download_receipt, name='download_receipt'),
    path('plan-receipt/<id>/', views.download_plan_receipt, name='download_plan_receipt'),
    path('contact',views.contact),
    path('thankyou',views.thankyou),
    path('logout',views.logout, name='user_logout'),
    path('runtrack',views.runtrack),
    path('apd',views.apd),
    path('plans',views.plans),
    path('payment/<str:type>',views.payment, name='payment'),
    path('save-plan-payment/', views.save_plan_payment, name='save_plan_payment'), 
    path('success', views.paymentsuccess),
    path('coaches', views.coaches),
    path('bmi/', views.bmi_tracker, name='bmi_tracker'),

    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='password_reset.html'), name='password_reset'),

    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'), name='password_reset_done'),

    path(
        'password-reset-confirm/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='registration/password_reset_confirm.html',
            success_url=reverse_lazy('password_reset_complete')  # ✅ inside as_view()
        ),
        name='password_reset_confirm'
    ),
    path(
        'password-reset-complete/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='registration/password_reset_complete.html'
        ),
        name='password_reset_complete'
    ),
]  

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)