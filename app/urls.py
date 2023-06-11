from django.urls import path
from .views import *
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('accounts/register/', RegisterView.as_view(), name='register'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('accounts/password_change/', PasswordChangeView.as_view(), name='password_change'),
    path('accounts/password_change/done', PasswordChangeDoneView.as_view(), name='password_change_done'),
    path('accounts/password/reset/', PasswordResetView.as_view(), name='my_password_reset'),
    path('accounts/password_reset/done/', PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('accounts/reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(),
         name='password_reset_confirm'),
    path('accounts/reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('', DashboardView.as_view(), name="dashboard"),


    path('upload/file', PointFileCreateView.as_view(), name="upload_file"),
    path('upload/<int:pk>/delete/', PointFileDeleteView.as_view(), name='point_delete'),
    path('create/post/', PostCreateView.as_view(), name='create_post'),
    path('posts/<int:pk>', PostsGetView.as_view(), name='my_posts'),

]
