from django.urls import path
from .views import *
from .restapis import *
from django.contrib.auth import views as auth_views
from . import views



urlpatterns = [
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('accounts/register/', RegisterView.as_view(), name='register'),
    path('accounts/register/invite', RegisterViewInvite.as_view(), name='register_with_company'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('accounts/password_change/', PasswordChangeView.as_view(), name='password_change'),
    path('accounts/password_change/done', PasswordChangeDoneView.as_view(), name='password_change_done'),
    path('accounts/password/reset/', PasswordResetView.as_view(), name='my_password_reset'),
    path('accounts/password_reset/done/', PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('accounts/reset/<uidb64>/<token>/', PasswordResetConfirmView.as_view(),name='password_reset_confirm'),
    path('accounts/reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('', BaseView.as_view(), name="base"),
    path('dashboard', DashboardView.as_view(), name="dashboard"),
    path('likeGraphApiview/', LikeGraphApi.as_view(), name="like_graph"),
    path('CommentGraphApiview/', CommentGraphApi.as_view(), name="comment_graph"),
    path('FollowersGraphApiview/', FollowersGraphApi.as_view(), name="followers_graph"),
    path('PostGraphApiview/', PostGraphApiView.as_view(), name="post_graph"),
    path('connect/page', ConnectPageView.as_view(), name='connect_page'),
    path('profile/', ProfileView.as_view(),name='my_profile'),
    path('users/', UserView.as_view(), name='my_user'),
    path('get/users/', UserSearchView.as_view(), name='get_users'),
    path('users/create/invite', UserCreateView.as_view(), name='create_user'),
    path('user/edit/', EditUserView.as_view(), name="edit_user"),
    path('assign_manager/', assign_manager.as_view(), name='assign_manager'),
    path('change_role/', change_role.as_view(), name='change_role'),
    path('delete_invite/', delete_invite.as_view(), name='delete_invite'),
    path('accept_invitation/', views.accept_invitation_view, name='accept_invitation_view'),
    path('reject_invitation/', views.reject_invitation_view, name='reject_invitation_view'),



    # path('<int:post_id>/publish/', views.publish_post, name='publish_post'),
    # path('<int:post_id>/schedule/', views.schedule_post, name='schedule_post'),



    path('upload/file', PointFileCreateView.as_view(), name="upload_file"),
    path('privacy_policy/', Privacy_policy.as_view(), name="privacy_policy"),
    path('upload/<int:pk>/delete/', PointFileDeleteView.as_view(), name='point_delete'),
    path('create/post/', PostCreateView.as_view(), name='create_post'),
    path('posts/<int:pk>', PostsGetView2.as_view(), name='my_posts'),
    # path('my_posts/<int:pk>', PostsGetView2.as_view(), name='my_posts2'),
    path('posts/detail/<int:post_id>/<int:page_id>', PostsDetailView.as_view(), name='my_detail_posts'),
    path('posts/like/<int:post_id>/<int:page_id>', LikeApiView.as_view(), name='like_apiview'),
    path('post_draft/<int:pk>', PostDraftView.as_view(), name='post_draft'),

    path('delete-post/<int:pk>/', PostDeleteView.as_view(), name='delete_post'),

    path('social/social/connections/', ConnectionView.as_view(), name="socialaccount_connections"),

    path('social/social/profile/', SocialProfileView.as_view(), name="social_profile"),
    path('social/social/profile/api/', SocialProfileAPI.as_view(), name="social_profile_api"),



    path('api_posts/', PostApiView.as_view(), name='api_posts'),


    path('social/page/', PageDataView.as_view(), name="page_data")

]
