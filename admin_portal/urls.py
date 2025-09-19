from django.urls import path 
from . import views

urlpatterns = [ 
    path('',views.user_admin),
    path('usermanage/',views.user_management, name="user_management"),
    path('useredit/<eid>/',views.user_edit),
    path('userdelete/<eid>/',views.user_delete),
    path('useradd/', views.user_add),
    path('create-event/', views.create_event, name="create_event"),
    path('eventlist/', views.eventlist, name='eventlist'),
    path('eventedit/<int:id>/', views.eventedit, name='edit_event'),
    path('eventdelete/<int:id>/', views.eventdelete, name='delete_event'),
    path('login/', views.admin_login, name='admin_login'),
    path('logout/', views.admin_logout, name='admin_logout'),
    path('event-payments/', views.event_payments, name='event_payments'),
    path('plan-payments/', views.plan_payments, name='plan_payments'),
] 