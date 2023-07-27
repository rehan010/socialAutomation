from django.urls import path
from .views import *
from .restapis import *
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
    path('', BaseView.as_view(), name="base"),
    path('dashboard', DashboardView.as_view(), name="dashboard"),
    path('connect/page',ConnectPageView.as_view(),name='connect_page'),
    path('profile/',ProfileView.as_view(),name='my_profile'),
    path('users/',UserView.as_view(),name='my_user'),
    path('get/users/',UserSearchView.as_view(),name='get_users'),
    path('users/create/',UserCreateView.as_view(),name='create_user'),

    # path('<int:post_id>/publish/', views.publish_post, name='publish_post'),
    # path('<int:post_id>/schedule/', views.schedule_post, name='schedule_post'),

    path("facebook/",FacebookRedirectUri.as_view(),name="facebook_redirect"),
    path('instagram/',InstagramRedirectUri.as_view(),name="instagram_redirect"),


    path('upload/file', PointFileCreateView.as_view(), name="upload_file"),
    path('upload/<int:pk>/delete/', PointFileDeleteView.as_view(), name='point_delete'),
    path('create/post/', PostCreateView.as_view(), name='create_post'),
    path('posts/<int:pk>', PostsGetView.as_view(), name='my_posts'),
    path('posts/detail/<int:post_id>/<int:page_id>', PostsDetailView.as_view(), name='my_detail_posts'),
    path('post_draft/<int:pk>', PostDraftView.as_view(), name='post_draft'),
    path("post/comment/", CommentPostView.as_view(),name = "comment_post"),



#     REST APIS

    path('getinsta/',instagramapi,name="geinsta"),

    path('createpost/',createpost,name = "createpost"),


    path("facebookhome/",facebookapi,name="facebookhome"),
    path("createfacebookpost/",createfacebookpost,name = "createfacebookpost")

]
