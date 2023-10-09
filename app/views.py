import json

from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.utils import user_username
from allauth.exceptions import ImmediateHttpResponse
from django.contrib.auth import views as auth_views
from django.contrib.auth import login,update_session_auth_hash
from django.http import response
from .signals import *
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import TemplateView, FormView,CreateView,DeleteView,UpdateView,ListView
from .forms import *
import requests
from .restapis import *
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from rest_framework.generics import ListAPIView,DestroyAPIView, RetrieveUpdateAPIView
from rest_framework.views import APIView
from django.db.models import Q ,Sum , Case, When, Value, BooleanField
from .serializer import *
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from rest_framework.pagination import PageNumberPagination
from django.views.decorators.csrf import csrf_exempt,csrf_protect
from django.utils.safestring import mark_safe
# from django.contrib.auth.models import User
from django.core.cache import cache

from .models import User
from allauth.socialaccount.models import EmailAddress, SocialAccount, SocialToken
from django.shortcuts import get_object_or_404
from rest_framework import filters
from django.core import serializers
from drf_link_header_pagination import LinkHeaderPagination
from .tasks import task_three
from google.oauth2 import id_token
from google.auth.transport import requests as auth_requests
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist

from django.shortcuts import render
from allauth.socialaccount.models import SocialToken
from django.utils.timezone import make_aware
from datetime import datetime, date, timedelta
# from .signals import post_update_signal
from django.contrib import messages
from django.contrib.auth import logout
from allauth.socialaccount.views import ConnectionsView
from django.utils.html import escape
from rest_framework import generics
from django.http import JsonResponse
from rest_framework.exceptions import NotFound
from django.conf import settings

from celery.result import AsyncResult
from django.contrib.auth.views import RedirectURLMixin
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login as auth_login , authenticate
from django.contrib.auth.password_validation import validate_password


# Import your custom filter






def get_id_token(access_token):
    # Specify the URL for the Google Tokeninfo API
    tokeninfo_url = 'https://www.googleapis.com/oauth2/v3/tokeninfo'

    # Parameters for the API request
    params = {'access_token': access_token}

    # Send a GET request to the Tokeninfo API
    response = requests.get(tokeninfo_url, params=params)

    if response.status_code == 200:
        token_info = response.json()
        id_token = token_info.get('sub')
        return id_token
    else:
        # Token verification failed

        return None


def verify_google_oauth_token(token):
    try:
        # Specify the CLIENT_ID of your Google OAuth application
        CLIENT_ID = '33836610262-gvtpcrjpbdefm0td6e0g7e4c76gut9s8.apps.googleusercontent.com'

        # Create a request object for token verification
        request = auth_requests.Request()

        # Verify the token using the CLIENT_ID and the request object
        id_info = id_token.verify_oauth2_token(token, request, CLIENT_ID)

        # If verification is successful, the id_info dictionary will contain
        # information about the token, such as user's email, name, etc.
        return id_info

    except ValueError as e:
        # Token verification failed

        return None

def my_business_view(request):
    # Retrieve the user's access token
    social_token = SocialToken.objects.get(account__user=request.user, account__provider='google')
    access_token = social_token.token

    # Set up the API endpoint and headers
    api_url = 'https://mybusiness.googleapis.com/v4/accounts/{account_id}/locations'
    headers = {'Authorization': f'Bearer {access_token}'}

    # Verify the access token
    request = auth_requests.Request()
    try:
        id_token_info = get_id_token(access_token)
        verified_info = verify_google_oauth_token(id_token_info)
        google_id = verified_info['sub']

    except ValueError as e:
        error_message = f"Error: Invalid access token - {str(e)}"
        return render(request, 'error.html', {'error_message': error_message})

    # Replace {account_id} in the API URL with the appropriate account ID
    api_url = api_url.format(account_id=google_id)

    # Make the API request
    response = requests.get(api_url, headers=headers)
    if response.status_code == 200:
        locations_data = response.json()
        # Process the retrieved data as needed
        # ...
        return render(request, 'my_business.html', {'locations': locations_data})
    else:
        error_message = f"Error: {response.status_code} - {response.text}"
        return render(request, 'error.html', {'error_message': error_message})

class BaseView(TemplateView):
    template_name = "registration/base.html"


class CustomLoginView(FormView):
    form_class = AuthenticationForm
    authentication_form = None
    template_name = "registration/login.html"
    success_url = reverse_lazy('dashboard')
    redirect_authenticated_user = False
    extra_context = None
    def form_valid(self, form):
       user = form.get_user()
       auth_login(self.request, user)

       if user.is_superuser:
           return redirect(reverse_lazy("my_user"))

       return super(CustomLoginView, self).form_valid(form)
    
    
    def form_invalid(self, form):
        user = User.objects.filter(username = form.cleaned_data['username'])
        # isauthenticate = authenticate(self.request,username = form.cleaned_data['username'],password = form.cleaned_data['password'])
        if user.exists():
            if user.first().is_active == False and user.first().is_deleted == True:
                form.errors.get("__all__").data.pop()
                form.add_error(None, 'Your access has been revoked by Root User')

            elif user.first().is_active == False:
                form.errors.get("__all__").data.pop()
                form.add_error(None, 'Please Request Root User To Grant Access')
        return super(CustomLoginView, self).form_invalid(form)
    
class ProfileView(LoginRequiredMixin,TemplateView):
    template_name = "registration/profile.html"

    def dispatch(self, request, *args, **kwargs):
        user = self.request.user

        if user.is_superuser:
            return redirect(reverse_lazy("my_user"))

        return super(ProfileView, self).dispatch(request)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        user_manager = user.manager

        if user_manager:
            invited_user = InviteEmploye.objects.filter(selected_user=user, invited_by=user_manager).first()
            role = invited_user.role
            context['user_role'] = role

        else:
            context['user_role'] = "ADMIN"

        return context
class UserView(LoginRequiredMixin,TemplateView):
    template_name = "registration/users.html"
    model = User

    def dispatch(self, request, *args, **kwargs):
        user = self.request.user
        if user.manager !=None:
            invite = InviteEmploye.objects.filter(email=user.email, status='ACCEPTED', permission='WRITE').first()

            if invite:
                return super().dispatch(request, *args, **kwargs)
            else:
                return redirect(reverse_lazy('dashboard'))
        else:
            return super().dispatch(request, *args, **kwargs)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # context['users'] = User.objects.filter(manager=self.request.user)
        # context['invites'] = InviteEmploye.objects.all()
        user_manager = self.request.user.manager
        if user_manager != None:
            context['invites_admin'] = InviteEmploye.objects.filter(Q(invited_by=self.request.user) | Q(invited_by=user_manager))
        context['invites'] = InviteEmploye.objects.filter(~Q(is_deleted=True), invited_by=self.request.user)
        context['users'] = User.objects.filter(Q(is_active=False), ~Q(company=None), manager=None)

        if self.request.user.is_superuser == True:
            companies = Company.objects.all()
            users_grouped_by_company = []
            for company in companies:

                owner = User.objects.filter(company = company , manager = None,is_deleted = False, is_active = True).first()
                if owner:
                    employee = InviteEmploye.objects.filter(~Q(selected_user__manager = None),selected_user__company= company,selected_user__is_deleted = False, selected_user__is_active = True)
                    user = {"owner": owner,"employee":employee}
                    users_grouped_by_company.append(user)
            context['user_grouped_by_company'] = users_grouped_by_company

        context['form'] = CustomUserCreationForm()
        return context

class UserSearchView(ListAPIView):
        queryset = User.objects.all()
        serializer_class = UserGetSerializer
        filter_backends = [filters.SearchFilter]
        search_fields = ['email', 'username']  # Add more fields to search by

        def get_queryset(self):
            queryset = super().get_queryset()
            search_query = self.request.query_params.get('q')
            if search_query:
                user_queryset = queryset.filter(Q(email__icontains=search_query) | Q(username__icontains=search_query), ~Q(manager=self.request.user), ~Q(id=self.request.user.id), Q(is_invited=False), Q(company=(self.request.user.company.all()).first()))
                # if len(InviteEmploye.objects.filter(Q(status='REJECTED'))) > 0:
                #     invite_queryset = InviteEmploye.objects.filter(
                #         Q(status='REJECTED')
                #     )
                #     queryset = user_queryset.union(invite_queryset)
                # else:
                queryset = user_queryset

                # Combine the querysets using the union operator |


            return queryset

import secrets

def generate_random_token(length=10):
    return secrets.token_urlsafe(length)

from django.template.loader import render_to_string
from django.core.mail import send_mail

class change_role(CreateView):
    model = InviteEmploye

    def post(self, request, *kwargs):
        if self.request.method == 'POST':
            data = json.loads(request.body)
            invite_id = data.get('user')
            role = data.get('role')
            manager_corp = data.get('manager_corp')
            permission = data.get('permission')
            if role == 'MEMBER' and manager_corp == 'False':
                permission = 'HIDE'
            elif role == 'ADMIN':
                permission = 'WRITE'
            invite = InviteEmploye.objects.get(pk=invite_id)
            selected_user = User.objects.get(pk=invite.selected_user.id)
            invite.role = role
            invite.manager_corp = manager_corp
            invite.permission = permission
            invite.save()
            return JsonResponse({'message': 'New role of' + ' ' + selected_user.username + ' ' + 'is' + ' ' + role + ' with permission' + ' ' + permission})
        else:
            return JsonResponse({'error': 'Selected user not found.'}, status=400)


class delete_invite(CreateView):
    model = InviteEmploye

    def post(self, request, *kwargs):
        if self.request.method == 'POST':
            data = json.loads(request.body)
            invite_id = data.get('user')
            invite = InviteEmploye.objects.get(pk=invite_id)
            current_time = timezone.now()
            if invite.selected_user:
                selected_user = User.objects.get(pk=invite.selected_user.id)
                for company in selected_user.company.all():
                    selected_user.company.remove(company)
                selected_user.manager = None
                selected_user.is_deleted = True
                selected_user.is_active = False
                selected_user.is_invited = False
                selected_user.save()
                invite.delete()

                email = selected_user.email
                context = {'recipient_name': selected_user.username}
                email_subject = "User's Permission Revoked"
                email_body = render_to_string('registration/delete_emails.html', context)

                # Send the email using Django's email functionality
                send_mail(email_subject, email_body, 'social_presence@gmail.com', [email])
            else:
                invite.delete()

            return JsonResponse({'message': 'Invitation of' + ' ' + invite.email + ' ' + 'deleted'})

        else:

            return JsonResponse({'error': 'Invite not found.'}, status=400)


from asgiref.sync import async_to_sync

class user_approval(APIView):
    model = User
    def approve_email(self,user):
       token = generate_random_token()
       invite_link = f"https://cloudwind-smartpresence-staging.com/accounts/login?token={token}"
       email = user.email

       context = {'recipient_name': user.username, 'invite_link': invite_link}
       email_subject = 'REQUEST APPROVED BY SMART PRESENCE'
       email_body = render_to_string('registration/emails.html', context)

       send_mail(email_subject, email_body, 'smart.presence.help@gmail.com', [email])




    def post(self, request, *kwargs):
        if self.request.method == 'POST':

            user_id = self.request.data.get('user')
            user = User.objects.get(id=user_id)
            user.is_active = True
            user.save()

            self.approve_email(user)

            return JsonResponse({'message': 'Request approved of' + user.username})

        else:

            return JsonResponse({'error': 'Invite not found.'}, status=400)

    def delete(self, request, *kwargs):
        if self.request.method == 'DELETE':

            user_id = self.request.GET.get('user')
            user = User.objects.get(id=user_id)
            token = generate_random_token()
            email = user.email

            context = {'recipient_name': user.username
                       }
            email_subject = 'REQUEST REJECTED BY SMART PRESENCE'
            email_body = render_to_string('registration/rejected_admin.html', context)

            # Send the email using Django's email functionality
            send_mail(email_subject, email_body, 'smart.presence.help@gmail.com', [email])
            # company = user.company.all().first()
            # created_company = Company.objects.get(pk=company)
            # created_company.delete()
            user.is_deleted = True
            user.is_rejected = True
            user.save()



            return JsonResponse({'message': 'Request approved of' + user.username})

        else:

            return JsonResponse({'error': 'Invite not found.'}, status=400)



class assign_manager(CreateView):
    model = InviteEmploye

    def post(self, request, *kwargs):
        if self.request.method == 'POST':
            data = json.loads(request.body)
            user_id = data.get('user')
            email = data.get('email')
            role = data.get('role')
            manager_corp = data.get('manager_corp')
            permission = data.get('permission')
            if role == 'MEMBER' and manager_corp == 'False':
                permission = "HIDE"
            if role == 'ADMIN':
                manager_corp = 'False'
                permission = "WRITE"

            if User.objects.filter(email=email).exists() or InviteEmploye.objects.filter(email=email).exists():
                return JsonResponse({'message': 'A user with this email already exists'})
            try:
                token = generate_random_token()
                expiration_date = timezone.now() + settings.TOKEN_EXPIRY

                if email is None:
                    selected_user = User.objects.get(pk=user_id)
                    invite = InviteEmploye(token=token, invited_by=self.request.user, status='PENDING', email=selected_user.email, selected_user=selected_user, role=role, permission=permission, manager_corp=manager_corp, expiration_date=expiration_date)
                    invite.save()
                    selected_user.is_invited = True
                    selected_user.save()
                   # invite_link = f"https://localhost:8000/accept_invitation?token={token}"
                    invite_link = f"https://cloudwind-smartpresence-staging.com/accept_invitation?token={token}"
                    email = selected_user.email
                    # email = 'anasurrehman5@gmail.com'

                    # Render the email template with the dynamic content
                    context = {'recipient_name': selected_user.username, 'invite_link': invite_link,
                               }
                    email_subject = 'Invitation to Join Our App'
                    email_body = render_to_string('registration/emails.html', context)

                    # Send the email using Django's email functionality
                    send_mail(email_subject, email_body, 'smart.presence.help@gmail.com', [email])
                else:
                    invite = InviteEmploye(token=token, invited_by=self.request.user, status='PENDING', email=email, role=role, permission=permission , manager_corp=manager_corp, expiration_date=expiration_date)
                    invite.save()


                    # invite_link = f"https://localhost:8000/accounts/register/invite?token={token}"
                    invite_link = f"https://cloudwind-smartpresence-staging.com/accounts/register/invite?token={token}"
                    # email = selected_user.email
                    email = email

                    # Render the email template with the dynamic content
                    context = {'recipient_name': 'User', 'invite_link': invite_link}
                    email_subject = 'Invitation to Join Our App'
                    email_body = render_to_string('registration/emails.html', context)

                    # Send the email using Django's email functionality
                    send_mail(email_subject, email_body, 'smart.presence.help@gmail.com', [email])

                return JsonResponse({'message': email})

            except User.DoesNotExist:
                return JsonResponse({'error': 'Selected user not found.'}, status=400)

        else:
            return JsonResponse({'error': 'Invalid request method.'}, status=405)



def accept_invitation_view(request):
    token = request.GET['token']
    invite = InviteEmploye.objects.get(token=token)
    user = User.objects.get(pk=invite.selected_user.id)
    current_time = timezone.now()

    try:
        invite = InviteEmploye.objects.get(token=token)
        if invite.expiration_date < current_time:
            invite.is_expired = True
            invite.delete()
            if request.user.is_authenticated:
                logout(request)
            return render(request, 'registration/invitation_failed.html')
        elif invite.is_deleted:
            if request.user.is_authenticated:
                logout(request)
            return render(request, 'registration/invitation_failed.html')
        else:
            invite.status = 'ACCEPTED'
            invite.save()
        login(request, user)

        return render(request, 'registration/invitation_complete.html')


    except InviteEmploye.DoesNotExist:
        # Token not found
        # Handle accordingly
        pass


def reject_invitation_view(request):
    token = request.GET['token']
    invite = InviteEmploye.objects.get(token=token)

    if invite:
        invite.status = 'REJECTED'
        invite.save()
    if invite.selected_user:
        user = User.objects.get(pk=invite.selected_user.id)
        user.company = None
        user.is_invited = False
        user.save()

    return render(request, 'registration/register.html')

class UserCreateView(LoginRequiredMixin,TemplateView):
    template_name = "registration/register.html"


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "registration/dashboard.html"
    def dispatch(self, request, *args, **kwargs):
        user = self.request.user

        if user.is_superuser:
            return redirect(reverse_lazy("my_user"))
        
        return super(DashboardView, self).dispatch(request)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = date.today()
        # year = timezone.now().year
        # curr_date = datetime.now()
        # before_date = datetime.now() + timedelta(days=-7)
        # week_before_date = before_date + timedelta(days=-7)
        # start_of_day = curr_date.replace(hour=0, minute=0, second=0, microsecond=0)
        # start = int(start_of_day.timestamp() * 1000)

        # Add your context data here
        if self.request.user.is_authenticated:
            user_manager = self.request.user.manager

            if user_manager != None:
                role = InviteEmploye.objects.get(selected_user=self.request.user, invited_by=self.request.user.manager)
                user_role = role.role
                user_permission = role.permission
                if user_permission == 'HIDE':

                    total_posts = PostModel.objects.filter( Q(status='PUBLISHED') | Q(status='FAILED'),user=self.request.user,  is_deleted=False)
                    sharepages = SharePage.objects.filter(user=self.request.user)

                else:
                    total_posts = PostModel.objects.filter(Q(user=self.request.user) | Q(user=self.request.user.manager), status='PUBLISHED')
                    sharepages = SharePage.objects.filter(Q(user=self.request.user) | Q(user=self.request.user.manager))


            else:
                invited = InviteEmploye.objects.filter(invited_by=self.request.user, status="ACCEPTED").values_list('selected_user', flat=True).distinct()

                total_posts = PostModel.objects.filter(Q(user=self.request.user.id) | Q(user__in=invited),Q(status='PUBLISHED') | Q(status='FAILED'), is_deleted = False)

                sharepages = SharePage.objects.filter(Q(user=self.request.user) | Q(user__in=invited))






            total_posts_count_today = total_posts.filter(Q(post_urn__org__provider='linkedin')|Q(post_urn__org__provider='facebook')|Q(post_urn__org__provider='instagram'), created_at__date__range = (today,today)).count()

            post_count_ln = total_posts.filter(post_urn__org__provider='linkedin', created_at__date__range = (today,today)).count()
            post_count_fb = total_posts.filter(post_urn__org__provider='facebook', created_at__date__range = (today,today)).count()
            post_count_insta = total_posts.filter(post_urn__org__provider='instagram', created_at__date__range = (today,today)).count()

            fb_share_pages = sharepages.filter(provider="facebook").distinct()
            insta_share_pages = sharepages.filter(provider="instagram").distinct()
            ln_share_pages = sharepages.filter(provider="linkedin").distinct()
            google_share_pages = sharepages.filter(provider="google").distinct()

            total_likes_facebook = SocialStats.objects.filter(org__in=fb_share_pages,
                                                              date=today).aggregate(Sum('t_likes'))['t_likes__sum']
            if total_likes_facebook is None:
                total_likes_facebook = 0


            total_likes_instagram = SocialStats.objects.filter(org__in=insta_share_pages,
                                                                  date=today).aggregate(Sum('t_likes'))['t_likes__sum']
            if total_likes_instagram is None:
                total_likes_instagram = 0
            total_likes_linkedin = SocialStats.objects.filter(org__in=ln_share_pages,
                                                              date=today).aggregate(Sum('t_likes'))['t_likes__sum']
            if total_likes_linkedin is None:
                total_likes_linkedin = 0
            total_likes_google = SocialStats.objects.filter(org__in=google_share_pages,
                                                                date=today).aggregate(Sum('t_likes'))['t_likes__sum']
            if total_likes_google is None:
                total_likes_google = 0


            total_comments_facebook = SocialStats.objects.filter(org__in=fb_share_pages,
                                                                 date=today).aggregate(Sum('t_comments'))['t_comments__sum']
            if total_comments_facebook is None:
                total_comments_facebook = 0
            total_comments_instagram = SocialStats.objects.filter(org__in=insta_share_pages,
                                                                  date=today).aggregate(Sum('t_comments'))['t_comments__sum']
            if total_comments_instagram is None:
                total_comments_instagram = 0
            total_comments_linkedin = SocialStats.objects.filter(org__in=ln_share_pages,
                                                                 date=today).aggregate(Sum('t_comments'))['t_comments__sum']
            if total_comments_linkedin is None:
                total_comments_linkedin = 0
            total_comments_google = SocialStats.objects.filter(org__in=google_share_pages,
                                                               date=today).aggregate(Sum('t_comments'))['t_comments__sum']
            if total_comments_google is None:
                total_comments_google = 0
            total_followers_facebook = SocialStats.objects.filter(org__in=fb_share_pages,
                                                                  date=today).aggregate(Sum('t_followers'))['t_followers__sum']
            if total_followers_facebook is None:
                total_followers_facebook = 0
            total_followers_instagram = SocialStats.objects.filter(org__in=insta_share_pages,
                                                                   date=today).aggregate(Sum('t_followers'))['t_followers__sum']
            if total_followers_instagram is None:
                total_followers_instagram = 0
            total_followers_linkedin = SocialStats.objects.filter(org__in=ln_share_pages,
                                                                  date=today).aggregate(Sum('t_followers'))['t_followers__sum']
            if total_followers_linkedin is None:
                total_followers_linkedin = 0
            total_followers_google = SocialStats.objects.filter(org__in=google_share_pages,
                                                                date=today).aggregate(Sum('t_followers'))['t_followers__sum']
            if total_followers_google is None:
                total_followers_google = 0

            # context['likes_today'] = likes_today
            context['linkedin_likes_today'] = total_likes_linkedin
            context['facebook_likes_today'] = total_likes_facebook
            context['instagram_likes_today'] = total_likes_instagram
            context['google_likes_today'] = total_likes_google
            # context['post_percentage'] = change_per
            # context['likes'] = likes_overall
            # context['comments_today'] = comments_today
            context['facebook_comments_today'] = total_comments_facebook
            context['instagram_comments_today'] = total_comments_instagram
            context['linkedin_comments_today'] = total_comments_linkedin
            context['google_comments_today'] = total_comments_linkedin
            # context['comments'] = comments_overall
            context['total_posts'] = total_posts_count_today
            # context['post_today'] = len(user_post)
            context['linkedin_post_today'] = post_count_ln
            context['facebook_post_today'] = post_count_fb
            context['instagram_post_today'] = post_count_insta
            # context['followers_today'] = followers_today
            context['facebook_new_followers'] = total_followers_facebook
            context['instagram_new_followers'] = total_followers_instagram
            context['google_new_followers'] = total_followers_google
            # context['followers_overall'] = followers_overall
            context['linkedin_new_followers'] = total_followers_linkedin


        return context



class DeleteCompanyApiView(APIView):

    def delete(self,request):
        try:
            userId = request.GET.get('userId')
            owner = User.objects.filter(id=userId).first()
            company = owner.company.first()

            users = User.objects.filter(~Q(manager=None), company=company, is_deleted=False, is_active=True)

            employees = InviteEmploye.objects.filter(selected_user__in=users, is_deleted=False)

            length = len(employees)
            i = 0
            while i < length:
                user = users[i]
                employee = employees[i]

                user.is_deleted = True
                user.is_active = False
                user.company.remove(company)
                user.manager = None
                user.save()

                employee.is_deleted = True
                employee.save()

                i = i + 1

            owner.is_deleted = True
            owner.is_active = False
            owner.company.remove(company)
            owner.manager = None
            owner.save()

            # Return a success response
            return JsonResponse({'message': 'success'})

        except Exception as e:
            # Handle the exception, log it, or return an error response
            return JsonResponse({'error': str(e)})



        # invited_employees = InviteEmploye.objects.filter()





class DashBoardCardView(APIView):

    def post(self, request):
        lock_key = self.lock_key_generator(self.request.user)

        user_manager = self.request.user.manager
        users = []
        if user_manager != None:
            role = InviteEmploye.objects.get(selected_user=self.request.user, invited_by=self.request.user.manager)
            user_role = role.role
            user_permission = role.permission
            if user_permission == 'READ' or user_permission == "WRITE":

                invited_users = InviteEmploye.objects.filter(invited_by=self.request.user, status="ACCEPTED").values_list('selected_user', flat=True).distinct()
                for in_user in invited_users:
                    users.append(in_user.id)
            else:
                pass
        else:
            invited_users = InviteEmploye.objects.filter(invited_by=self.request.user, status="ACCEPTED").values_list('selected_user', flat=True).distinct()
            for in_user in invited_users:
                users.append(in_user)
        users.append(self.request.user.id)


        task = task_three.apply_async(args=[users,lock_key])

        return Response({'task_id': task.id})



    def get(self, request):

        task_id = self.request.GET.get('task_id')
        task = AsyncResult(task_id)
        if task.ready():
            if task.successful():
                user_manager = self.request.user.manager
                today = date.today()
                if user_manager != None:
                    role = InviteEmploye.objects.get(selected_user=self.request.user,
                                                     invited_by=self.request.user.manager)
                    user_role = role.role
                    user_permission = role.permission
                    if user_permission == 'HIDE':

                        total_posts = PostModel.objects.filter(user=self.request.user, status='PUBLISHED',
                                                               is_deleted=False)
                        sharepages = SharePage.objects.filter(user=self.request.user)

                    else:
                        total_posts = PostModel.objects.filter(
                            Q(user=self.request.user) | Q(user=self.request.user.manager), status='PUBLISHED')
                        sharepages = SharePage.objects.filter(
                            Q(user=self.request.user) | Q(user=self.request.user.manager))


                else:
                    invited = InviteEmploye.objects.filter(invited_by=self.request.user, status="ACCEPTED").values_list(
                        'selected_user', flat=True).distinct()

                    total_posts = PostModel.objects.filter(Q(user=self.request.user.id) | Q(user__in=invited),
                                                           status='PUBLISHED', is_deleted=False)

                    sharepages = SharePage.objects.filter(Q(user=self.request.user) | Q(user__in=invited))

                total_posts_count_today = total_posts.filter(
                    Q(post_urn__org__provider='linkedin') | Q(post_urn__org__provider='facebook') | Q(
                        post_urn__org__provider='instagram'), created_at__date__range=(today, today)).count()

                post_count_ln = total_posts.filter(post_urn__org__provider='linkedin',
                                                   created_at__date__range=(today, today)).count()
                post_count_fb = total_posts.filter(post_urn__org__provider='facebook',
                                                   created_at__date__range=(today, today)).count()
                post_count_insta = total_posts.filter(post_urn__org__provider='instagram',
                                                      created_at__date__range=(today, today)).count()

                fb_share_pages = sharepages.filter(provider="facebook").distinct()
                insta_share_pages = sharepages.filter(provider="instagram").distinct()
                ln_share_pages = sharepages.filter(provider="linkedin").distinct()
                google_share_pages = sharepages.filter(provider="google").distinct()

                total_likes_facebook = SocialStats.objects.filter(org__in=fb_share_pages,
                                                                  date=today).aggregate(Sum('t_likes'))['t_likes__sum']
                if total_likes_facebook is None:
                    total_likes_facebook = 0

                total_likes_instagram = SocialStats.objects.filter(org__in=insta_share_pages,
                                                                   date=today).aggregate(Sum('t_likes'))['t_likes__sum']
                if total_likes_instagram is None:
                    total_likes_instagram = 0
                total_likes_linkedin = SocialStats.objects.filter(org__in=ln_share_pages,
                                                                  date=today).aggregate(Sum('t_likes'))['t_likes__sum']
                if total_likes_linkedin is None:
                    total_likes_linkedin = 0
                total_likes_google = SocialStats.objects.filter(org__in=google_share_pages,
                                                                date=today).aggregate(Sum('t_likes'))['t_likes__sum']
                if total_likes_google is None:
                    total_likes_google = 0

                total_comments_facebook = SocialStats.objects.filter(org__in=fb_share_pages,
                                                                     date=today).aggregate(Sum('t_comments'))[
                    't_comments__sum']
                if total_comments_facebook is None:
                    total_comments_facebook = 0
                total_comments_instagram = SocialStats.objects.filter(org__in=insta_share_pages,
                                                                      date=today).aggregate(Sum('t_comments'))[
                    't_comments__sum']
                if total_comments_instagram is None:
                    total_comments_instagram = 0
                total_comments_linkedin = SocialStats.objects.filter(org__in=ln_share_pages,
                                                                     date=today).aggregate(Sum('t_comments'))[
                    't_comments__sum']
                if total_comments_linkedin is None:
                    total_comments_linkedin = 0
                total_comments_google = SocialStats.objects.filter(org__in=google_share_pages,
                                                                   date=today).aggregate(Sum('t_comments'))[
                    't_comments__sum']
                if total_comments_google is None:
                    total_comments_google = 0
                total_followers_facebook = SocialStats.objects.filter(org__in=fb_share_pages,
                                                                      date=today).aggregate(Sum('t_followers'))[
                    't_followers__sum']
                if total_followers_facebook is None:
                    total_followers_facebook = 0
                total_followers_instagram = SocialStats.objects.filter(org__in=insta_share_pages,
                                                                       date=today).aggregate(Sum('t_followers'))[
                    't_followers__sum']
                if total_followers_instagram is None:
                    total_followers_instagram = 0
                total_followers_linkedin = SocialStats.objects.filter(org__in=ln_share_pages,
                                                                      date=today).aggregate(Sum('t_followers'))[
                    't_followers__sum']
                if total_followers_linkedin is None:
                    total_followers_linkedin = 0
                total_followers_google = SocialStats.objects.filter(org__in=google_share_pages,
                                                                    date=today).aggregate(Sum('t_followers'))[
                    't_followers__sum']
                if total_followers_google is None:
                    total_followers_google = 0

                context = dict()
                context['linkedin_likes_today'] = total_likes_linkedin
                context['facebook_likes_today'] = total_likes_facebook
                context['instagram_likes_today'] = total_likes_instagram
                context['google_likes_today'] = total_likes_google
                context['facebook_comments_today'] = total_comments_facebook
                context['instagram_comments_today'] = total_comments_instagram
                context['linkedin_comments_today'] = total_comments_linkedin
                context['google_comments_today'] = 0
                context['total_posts'] = total_posts_count_today
                context['linkedin_post_today'] = post_count_ln
                context['google_post_today'] = 0
                context['facebook_post_today'] = post_count_fb
                context['instagram_post_today'] = post_count_insta
                context['facebook_new_followers'] = total_followers_facebook
                context['instagram_new_followers'] = total_followers_instagram
                context['google_new_followers'] = total_followers_google
                context['linkedin_new_followers'] = total_followers_linkedin
                return Response({'status': 'SUCCESS', 'result': context})
            else:
                return Response({'status': 'FAILURE', 'result': 'Task failed'})
        else:
            return Response({'status': 'PENDING', 'result': None})


    def lock_key_generator(self,user):
        return f"task_lock:{user.id}"


class PasswordResetView(auth_views.PasswordResetView):
    template_name = "registration/my_password_reset_form.html"
    success_url = reverse_lazy('my_password_reset')
    
    def get_success_url(self):
        return self.success_url + "?reset=done"




class PasswordResetDoneView(auth_views.PasswordResetDoneView):
    template_name = "registration/my_password_reset_done.html"
    success_url = reverse_lazy("password_change_done")

class PasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = "registration/password_reset_confirm.html"
    success_url = reverse_lazy("login")
    





class ConnectPageView(LoginRequiredMixin, CreateView):
    model = SharePage
    form_class = SharePageForm
    template_name = 'social/connection.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user  # Set the user to the logged-in user
        social = SocialAccount.objects.filter(user=user.id)
        access_token = {}
        for _ in social:
            access_token[_.provider] = SocialToken.objects.filter(account_id=_)

        my_list = []
        data=my_list

        # context
        # 'point_files': point_files

        context = {'data': data}
        return context

    def post(self, request, args, *kwargs):
        ids = request.POST.getlist('selected_keys')
        user = self.request.user
        social = SocialAccount.objects.get(user=user.id)

        share_page=SharePage.objects.filter(user=social).exclude(organizations_id__in=ids)
        if share_page.count() > 0:
            share_page.delete()
        for id in ids:
            share = SharePage.objects.filter(organizations_id=id)
            if share.count() > 0:
                pass
            else:
                SharePage.objects.create(user=self.request.user,organizations_id=id)

        return redirect(reverse("ln_posts", kwargs={'pk': self.request.user.id}))



class PasswordChangeDoneView(LoginRequiredMixin,auth_views.PasswordChangeDoneView):
    template_name = "registration/my_password_change_done.html"


class PasswordChangeView(LoginRequiredMixin,auth_views.PasswordChangeView):
    template_name = "registration/my_password_change_form.html"


class RegisterView(FormView):
    template_name = "registration/register.html"
    form_class = CustomUserCreationForm
    
    def form_invalid(self, form):

        logged_in_user = self.request.user.is_superuser
        if logged_in_user:
            return redirect(reverse("my_user"))
        
        return super(RegisterView, self).form_invalid(form)

    def form_valid(self, form):
        user = form.save(commit=False)
        company_name = form.cleaned_data.get('company_name')
        email = form.cleaned_data.get('email')
        user_email = User.objects.filter(email=email)

        user_company = Company.objects.filter(name=company_name)
        if user_company.exists():
            form.add_error('company_name', 'A Company with this name already exists.')

            return self.form_invalid(form)

        if user_email.exists():
            form.add_error('email', 'A user with this email already exists.')
            return self.form_invalid(form)

        else:
            user.save()
        # Check if the company name is provided
        if company_name:
            # Create a new company if it doesn't exist
            company, created = Company.objects.get_or_create(name=company_name)
            user.company.add(company)
        else:
            # If no company name is provided, create a new company with the user's username
            company, created = Company.objects.get_or_create(name=user.username)
            user.company.add(company)
        logged_in_user =  self.request.user.is_superuser
        if logged_in_user == True:
            user.is_active = True
            user.save()

            return redirect(reverse("my_user"))

        else:
            user.is_active = False
            user.save()
            return redirect(reverse("login"))



class CreateUserFormView(FormView,LoginRequiredMixin):
    template_name = 'registration/create_user.html'
    form_class = CustomUserCreationForm

    def dispatch(self, request, *args, **kwargs):

        user = self.request.user
        if user.is_superuser == False:
            return redirect(reverse_lazy("dashboard"))

        return super(CreateUserFormView, self).dispatch(request)
    def form_valid(self, form):
        user = form.save(commit=False)
        company_name = form.cleaned_data.get('company_name')
        email = form.cleaned_data.get('email')
        user_email = User.objects.filter(email=email)

        user_company = Company.objects.filter(name=company_name)
        if user_company.exists():
            form.add_error('company_name', 'A Company with this name already exists.')

            return self.form_invalid(form)

        if user_email.exists():
            form.add_error('email', 'A user with this email already exists.')
            return self.form_invalid(form)

        else:
            user.save()
        # Check if the company name is provided
        if company_name:
            # Create a new company if it doesn't exist
            company, created = Company.objects.get_or_create(name=company_name)
            user.company.add(company)
        else:
            # If no company name is provided, create a new company with the user's username
            company, created = Company.objects.get_or_create(name=user.username)
            user.company.add(company)
        logged_in_user =  self.request.user.is_superuser
        if logged_in_user == True:
            user.is_active = True
            user.save()

        return redirect(reverse("my_user"))



class RegisterViewInvite(FormView):
    template_name = "registration/invitation.html"
    form_class = CustomUserInvitationForm

    def dispatch(self, request, *args, **kwargs):
        user = self.request.user

        if user.is_superuser:
            return redirect(reverse_lazy("my_user"))

        return super(RegisterViewInvite, self).dispatch(request)
    def get(self, request, *args, **kwargs):
        token = self.request.GET['token']
        invite = InviteEmploye.objects.get(token=token)
        current_time = timezone.now()

        if invite.expiration_date < current_time:
            invite.delete()

            return render(request, 'registration/invitation_failed.html')

        elif invite.is_deleted:
            if self.request.user.is_authenticated:
                logout(request)

            return render(request, 'registration/invitation_failed.html')
        elif invite.invited_by.is_deleted == True:
            if self.request.user.is_authenticated:
                logout(request)

            return render(request, 'registration/invitation_failed.html')

        else:

            if self.request.user.is_authenticated:
                logout(request)
            return super().get(request, *args, **kwargs)

    def form_valid(self, form):

        user = form.save(commit=False)
        token = self.request.GET['token']
        email = self.request.POST.get('email')
        email_invite = InviteEmploye.objects.filter(selected_user__email=email)
        email_user = User.objects.filter(email=email)
        if email_invite.exists():
            form.add_error('email', 'A user with this email already exists.')
            return self.form_invalid(form)
        if email_user.exists():
            form.add_error('email', 'A user with this email already exists.')
            return self.form_invalid(form)



        company_name = form.cleaned_data.get('company').first()
        c_name = Company.objects.get(name=company_name)

        try:
            invited = InviteEmploye.objects.get(token=token, email=email)
        except InviteEmploye.DoesNotExist:
            invited = None

        if invited != None:
            user.save()
        else:
            form.add_error('email', 'Invite was sent to a different Email address')
            return self.form_invalid(form)
        user.manager = invited.invited_by
        user.company.add(c_name)
        user.save()
        invited.selected_user = user
        invited.status = 'ACCEPTED'
        invited.save()



        login(self.request, user)
        return redirect(reverse("dashboard"))


    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        token = self.request.GET['token']
        invite = InviteEmploye.objects.get(token=token)
        if invite:
            # Retrieve the 'company' query parameter from the URL and pass it to the form
            kwargs['initial'] = {'company': (invite.invited_by.company.all()).first()}
        else:
            kwargs['initial'] = {'company': 'Type in your own company'}

        return kwargs

class PrivacyPolicyView(TemplateView):
    template_name = 'registration/privacy_policy.html'


class PointFileCreateView(LoginRequiredMixin, CreateView):
    model = PointFileModel
    form_class = PointFileModelForm
    template_name = 'social/create_point_file.html'

    def form_valid(self, form):

        point_file = form.save(commit=False)
        point_file.user = self.request.user  # Set the user to the logged-in user
        point_file.save()
        file_path = point_file.point_file.path  # Replace with the path to your text file

        with open(file_path, 'r') as file:
            for line in file:
                lat, lon = line.strip().split(',')
                lat_long_point = LatLongModel(latitude=lat, longitude=lon,file=point_file)
                lat_long_point.save()

        return redirect(reverse("dashboard"))


class PointFileDeleteView(LoginRequiredMixin,DeleteView):
    model = PointFileModel
    success_url = reverse_lazy('dashboard')
    template_name = 'social/file_confirm_delete.html'

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset

def create_post_with_image(access_token, message, image_path):
    url = "https://graph.facebook.com/v17.0/me/photos"
    params = {
        "access_token": access_token,
        "message": message
    }
    files = {
        "source": open(image_path, "rb")
    }
    response = requests.post(url, params=params, files=files)
    return response.json()


class PostCreateView(CreateView):
    # model = PostModel
    form_class = PostModelForm
    template_name = 'social/create_post.html'
    success_url = reverse_lazy('my_posts')

    def dispatch(self, request, *args, **kwargs):
        user = self.request.user

        if user.is_superuser:
            return redirect(reverse_lazy("my_user"))

        return super(PostCreateView, self).dispatch(request)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comment_check = True
        context = {'comment_check': comment_check, 'form': self.get_form()}
        return context


    def form_valid(self, form):
        requestdata = dict(self.request.POST)
        context = self.request.session.get('context')


        linkedin_errors = linkedin_validator(self.request)
        facebook_errors = facebook_validator(self.request)
        instagram_errors = instagram_validator(self.request)



        if facebook_errors or instagram_errors or linkedin_errors:
            for errors in facebook_errors:
                messages.error(self.request,facebook_errors[errors])

            for errors in instagram_errors:
                messages.error(self.request, instagram_errors[errors])

            for errors in linkedin_errors:
                messages.error(self.request, linkedin_errors[errors])

            return self.form_invalid(form)




        requestdata.pop("csrfmiddlewaretoken")
        caption = requestdata.pop("post")
        post = form.save(commit=False)
        post.user = self.request.user
        # social = SocialAccount.objects.get(user=self.request.user, provider='linkedin_oauth2')
        post.post = caption[0]

        comment_check = form.cleaned_data.get('comment_check')
        if comment_check:
            post.comment_check = True
        else:
            post.comment_check = False
        action = self.request.POST.get('action', '')
        if action == 'publish':
            post.status = 'PROCESSING'
            post.publish_check = True
        elif action == 'schedule':
            post.status = 'SCHEDULED'
            post.publish_check = False
            schedule_date = self.request.POST.get('date')
            schedule_time = self.request.POST.get('time')
            schedule_datetime_str = f"{schedule_date} {schedule_time}"

            if schedule_datetime_str:
                schedule_datetime = datetime.strptime(schedule_datetime_str, '%Y-%m-%d %H:%M')
                post.schedule_datetime = schedule_datetime

        else:
            post.status == 'DRAFT'
            post.publish_check = False
        share_pages = []
        if requestdata.get("linkedin") or requestdata.get('facebook') or requestdata.get('instagram'):
            for page in requestdata.get("linkedin") or []:
                i = 0
                while context.get('linkedin')[i]['id'] != page:
                    i += 1
                info = context.get('linkedin').pop(i)
                user = User.objects.get(id = info['user'])
                share_page, created = SharePage.objects.get_or_create(org_id=page, provider='linkedin', user=user, name=info['name'])

                if created:
                    share_page.access_token = SocialToken.objects.get(account__user__id=info['user'], app__provider="linkedin_oauth2").token
                    share_page.save()
                share_pages.append(share_page)

            for page in requestdata.get("facebook") or []:
                i = 0
                while context.get('facebook')[i].get('id') != page:
                    i += 1

                info = context.get('facebook').pop(i)

                ispageexist = SharePage.objects.filter(org_id=info.get('id'),user__id = info['user']).exists()

                if ispageexist:
                    sharepage = SharePage.objects.get(org_id=info.get('id'),user__id = info['user'])
                    share_pages.append(sharepage)

                else:
                    user = User.objects.get(id=info['user'])
                    sharepage = SharePage.objects.create(user=user)
                    sharepage.name = info.get('name')
                    sharepage.access_token = info.get('access_token')
                    sharepage.org_id = info.get('id')
                    sharepage.provider = "facebook"
                    sharepage.save()

                    share_pages.append(sharepage)
            for page in requestdata.get("instagram") or []:
                i = 0
                while context.get('instagram')[i].get('id') != page:
                    i += 1


                info = context.get('instagram').pop(i)
                ispageexist = SharePage.objects.filter(org_id=info.get('id'), user__id=info['user']).exists()

                # Store Shared Page
                if ispageexist:
                    sharepage = SharePage.objects.get(org_id=info.get('id'),user__id=info['user'])
                    share_pages.append(sharepage)

                else:
                    user = User.objects.get(id=info['user'])
                    sharepage = SharePage.objects.create(user=user)
                    sharepage.name = info.get('name')
                    sharepage.access_token = SocialToken.objects.get(account__user__id = info['user'], app__provider = "facebook").token
                    sharepage.org_id = info.get('id')
                    sharepage.provider = "instagram"
                    sharepage.save()
                    share_pages.append(sharepage)

        else:
            from django.http import Http404
            raise Http404("Please Select a Page To Share")
        images = self.request.FILES.getlist('images')
        post.save()
        image_object = []
        if images:
            for image in images:
                image_model = ImageModel(image=image)
                image_model.save()
                image_object.append(image_model)
        post.images.add(*image_object)

        post.prepost_page.add(*share_pages)

        return redirect(reverse("my_posts", kwargs={'pk': self.request.user.id}))

class LikeGraphApi(APIView):

    def post(self,request):
        post_data = self.request.data

        starting_date = post_data.get('start')
        end_date = post_data.get('end')

        starting_date = datetime.strptime(starting_date, "%Y-%m-%d")
        end_date = datetime.strptime(end_date, "%Y-%m-%d")

        user = self.request.user

        if user.manager !=None:
            role = InviteEmploye.objects.get(selected_user=self.request.user, invited_by=self.request.user.manager)
            user_role = role.role
            user_permission = role.permission
            if user_permission == 'HIDE':
                sharepages = SharePage.objects.filter(user=self.request.user)
            else:
                sharepages = SharePage.objects.filter(Q(user=self.request.user) | Q(user=self.request.user.manager))
        else:
            invited = InviteEmploye.objects.filter(invited_by=self.request.user, status="ACCEPTED")
            invites = []
            for user in invited:
                invited_users_id = user.selected_user.id
                invites.append(invited_users_id)

            sharepages = SharePage.objects.filter(Q(user=self.request.user) | Q(user__in=invites))




        fb_share_pages = sharepages.filter(provider = "facebook").distinct()
        insta_share_pages = sharepages.filter(provider = "instagram").distinct()
        ln_share_pages = sharepages.filter(provider = "linkedin").distinct()
        google_share_pages = sharepages.filter(provider = "google").distinct()

        result_fb = []
        result_ln = []
        result_insta = []
        result_google = []
        labels = []

        starting = starting_date

        while starting <= end_date:

            total_likes_facebook = SocialStats.objects.filter(org__in=fb_share_pages,
                                                                       date = starting).aggregate(Sum('t_likes'))['t_likes__sum']

            total_likes_instagram = SocialStats.objects.filter(org__in=insta_share_pages,
                                                               date=starting).aggregate(Sum('t_likes'))['t_likes__sum']

            total_likes_linkedin = SocialStats.objects.filter(org__in=ln_share_pages,
                                                              date=starting).aggregate(Sum('t_likes'))['t_likes__sum']

            total_likes_google = SocialStats.objects.filter(org__in=google_share_pages,
                                                            date=starting).aggregate(Sum('t_likes'))['t_likes__sum']

            if not total_likes_facebook:
                total_likes_facebook = 0

            if not total_likes_instagram:
                total_likes_instagram = 0

            if not total_likes_linkedin:
                total_likes_linkedin = 0

            if not total_likes_google:
                total_likes_google = 0




            labels.append(starting.strftime("%Y-%m-%d"))
            result_fb.append(total_likes_facebook)
            result_ln.append(total_likes_linkedin)
            result_insta.append(total_likes_instagram)
            result_google.append(total_likes_google)

            starting = starting + timedelta(days=1)


        data = {
            'labels' : labels,
            'facebook': result_fb,
            'instagram':result_insta,
            'linkedin': result_ln,
            'google': result_google
        }
        return JsonResponse(data)
class CommentGraphApi(APIView):

    def post(self,request):
        post_data = self.request.data

        starting_date = post_data.get('start')
        end_date = post_data.get('end')

        starting_date = datetime.strptime(starting_date, "%Y-%m-%d")
        end_date = datetime.strptime(end_date, "%Y-%m-%d")

        user = self.request.user

        if user.manager !=None:
            role = InviteEmploye.objects.get(selected_user=self.request.user, invited_by=self.request.user.manager)
            user_role = role.role
            user_permission = role.permission
            if user_permission == 'HIDE':
                sharepages = SharePage.objects.filter(user=self.request.user)
            else:
                sharepages = SharePage.objects.filter(Q(user=self.request.user) | Q(user=self.request.user.manager))
        else:
            invited = InviteEmploye.objects.filter(invited_by=self.request.user, status="ACCEPTED")
            invites = []
            for user in invited:
                invited_users_id = user.selected_user.id
                invites.append(invited_users_id)

            sharepages = SharePage.objects.filter(Q(user=self.request.user) | Q(user__in=invites))




        fb_share_pages = sharepages.filter(provider = "facebook").distinct()
        insta_share_pages = sharepages.filter(provider = "instagram").distinct()
        ln_share_pages = sharepages.filter(provider = "linkedin").distinct()
        google_share_pages = sharepages.filter(provider = "google").distinct()

        result_fb = []
        result_ln = []
        result_insta = []
        result_google = []
        labels = []

        starting = starting_date

        while starting <= end_date:

            total_comments_facebook = SocialStats.objects.filter(org__in=fb_share_pages,
                                                                       date = starting).aggregate(Sum('t_comments'))['t_comments__sum']

            total_comments_instagram = SocialStats.objects.filter(org__in=insta_share_pages,
                                                               date=starting).aggregate(Sum('t_comments'))['t_comments__sum']

            total_comments_linkedin = SocialStats.objects.filter(org__in=ln_share_pages,
                                                              date=starting).aggregate(Sum('t_comments'))['t_comments__sum']

            total_comments_google = SocialStats.objects.filter(org__in=google_share_pages,
                                                            date=starting).aggregate(Sum('t_comments'))['t_comments__sum']

            if not total_comments_facebook:
                total_comments_facebook = 0

            if not total_comments_instagram:
                total_comments_instagram = 0

            if not total_comments_linkedin:
                total_comments_linkedin = 0

            if not total_comments_google:
                total_comments_google = 0




            labels.append(starting.strftime("%Y-%m-%d"))
            result_fb.append(total_comments_facebook)
            result_ln.append(total_comments_linkedin)
            result_insta.append(total_comments_instagram)
            result_google.append(total_comments_google)

            starting = starting + timedelta(days=1)


        data = {
            'labels' : labels,
            'facebook': result_fb,
            'instagram':result_insta,
            'linkedin': result_ln,
            'google': result_google
        }
        return JsonResponse(data)


class FollowersGraphApi(APIView):

    def post(self,request):
        post_data = self.request.data

        starting_date = post_data.get('start')
        end_date = post_data.get('end')

        starting_date = datetime.strptime(starting_date, "%Y-%m-%d")
        end_date = datetime.strptime(end_date, "%Y-%m-%d")

        user = self.request.user

        if user.manager !=None:
            role = InviteEmploye.objects.get(selected_user=self.request.user, invited_by=self.request.user.manager)
            user_role = role.role
            user_permission = role.permission
            if user_permission == 'HIDE':
                sharepages = SharePage.objects.filter(user=self.request.user)
            else:
                sharepages = SharePage.objects.filter(Q(user=self.request.user) | Q(user=self.request.user.manager))
        else:
            invited = InviteEmploye.objects.filter(invited_by=self.request.user, status="ACCEPTED")
            invites = []
            for user in invited:
                invited_users_id = user.selected_user.id
                invites.append(invited_users_id)

            sharepages = SharePage.objects.filter(Q(user=self.request.user) | Q(user__in=invites))




        fb_share_pages = sharepages.filter(provider = "facebook").distinct()
        insta_share_pages = sharepages.filter(provider = "instagram").distinct()
        ln_share_pages = sharepages.filter(provider = "linkedin").distinct()
        google_share_pages = sharepages.filter(provider = "google").distinct()

        result_fb = []
        result_ln = []
        result_insta = []
        result_google = []
        labels = []

        starting = starting_date

        while starting <= end_date:

            total_followers_facebook = SocialStats.objects.filter(org__in=fb_share_pages,
                                                                       date = starting).aggregate(Sum('t_followers'))['t_followers__sum']

            total_followers_instagram = SocialStats.objects.filter(org__in=insta_share_pages,
                                                               date=starting).aggregate(Sum('t_followers'))['t_followers__sum']

            total_followers_linkedin = SocialStats.objects.filter(org__in=ln_share_pages,
                                                              date=starting).aggregate(Sum('t_followers'))['t_followers__sum']

            total_followers_google = SocialStats.objects.filter(org__in=google_share_pages,
                                                            date=starting).aggregate(Sum('t_followers'))['t_followers__sum']

            if not total_followers_facebook:
                total_followers_facebook = 0

            if not total_followers_instagram:
                total_followers_instagram = 0

            if not total_followers_linkedin:
                total_followers_linkedin = 0

            if not total_followers_google:
                total_followers_google = 0




            labels.append(starting.strftime("%Y-%m-%d"))
            result_fb.append(total_followers_facebook)
            result_ln.append(total_followers_linkedin)
            result_insta.append(total_followers_instagram)
            result_google.append(total_followers_google)

            starting = starting + timedelta(days=1)


        data = {
            'labels' : labels,
            'facebook': result_fb,
            'instagram':result_insta,
            'linkedin': result_ln,
            'google': result_google
        }
        return JsonResponse(data)



class PostGraphApiView(APIView):
    def post(self,request):
        post_data = self.request.data

        starting_date = post_data.get('start')
        end_date = post_data.get('end')

        starting_date = datetime.strptime(starting_date, "%Y-%m-%d")
        end_date = datetime.strptime(end_date, "%Y-%m-%d")

        user = self.request.user

        if user.manager !=None:
            role = InviteEmploye.objects.get(selected_user=self.request.user, invited_by=self.request.user.manager)
            user_role = role.role
            user_permission = role.permission
            if user_permission == 'HIDE':
                total_posts = PostModel.objects.filter(Q(status='PUBLISHED') | Q(status='FAILED'), user=self.request.user, is_deleted=False)
            else:
                total_posts = PostModel.objects.filter(Q(user=self.request.user) | Q(user=self.request.user.manager),Q(status='PUBLISHED') | Q(status='FAILED'), is_deleted=False)

        else:
            invited = InviteEmploye.objects.filter(invited_by=self.request.user, status="ACCEPTED")
            invites = []
            for user in invited:
                invited_users_id = user.selected_user.id
                invites.append(invited_users_id)
            total_posts = PostModel.objects.filter(Q(user=self.request.user.id) | Q(user__in=invites),Q(status='PUBLISHED') | Q(status='FAILED'), is_deleted=False)


        result_fb = []
        result_ln = []
        result_insta = []
        result_google = []
        labels = []

        starting = starting_date

        while starting <= end_date:

            post_count_ln = total_posts.filter(post_urn__org__provider='linkedin', created_at__date__range = (starting,starting)).count()
            post_count_fb = total_posts.filter(post_urn__org__provider='facebook', created_at__date__range = (starting,starting)).count()
            post_count_insta = total_posts.filter(post_urn__org__provider='instagram', created_at__date__range = (starting,starting)).count()
            post_count_google = total_posts.filter(post_urn__org__provider='google', created_at__date__range = (starting,starting)).count()

            # if not total_comments_facebook:
            #     total_comments_facebook = 0
            #
            # if not total_comments_instagram:
            #     total_comments_instagram = 0
            #
            # if not total_comments_linkedin:
            #     total_comments_linkedin = 0
            #
            # if not total_comments_google:
            #     total_comments_google = 0
            labels.append(starting.strftime("%Y-%m-%d"))
            result_fb.append(post_count_fb)
            result_ln.append(post_count_ln)
            result_insta.append(post_count_insta)
            result_google.append(post_count_google)

            starting = starting + timedelta(days=1)


        data = {
            'labels' : labels,
            'facebook': result_fb,
            'instagram':result_insta,
            'linkedin': result_ln,
            'google': result_google
        }
        return JsonResponse(data)









class PageDataView(APIView):
    def get(self, request):
        user = self.request.user  # Set the user to the logged-in user
        user_manager = self.request.user.manager

        if user_manager:
            selected_user = InviteEmploye.objects.get(selected_user=self.request.user, invited_by=self.request.user.manager)
            permission = selected_user.permission

            if permission == "WRITE":
                social = SocialAccount.objects.filter(Q(user=user.id) | Q(user=user_manager.id))
            else:
                social = SocialAccount.objects.filter(Q(user=user.id))

        else:
            social = SocialAccount.objects.filter(Q(user=user.id))
        access_token = {}
        data = {}

        try:
            post_id = request.query_params.get('pk')
            if post_id:
                postIds = []
                post = PostModel.objects.get(pk=post_id)
                for page in post.prepost_page.all():
                    postIds.append(page.org_id)
                data['posts'] = postIds
        except Exception as e:
            e



        for _ in social:
            if access_token.get(_.user.username) == None:
                access_token[_.user.username] = {}
                access_token[_.user.username][_.provider] =  SocialToken.objects.filter(account_id=_)[0].token
                access_token[_.user.username]['id'] =  _.user.id


            else:
                access_token[_.user.username][_.provider] = SocialToken.objects.filter(account_id=_)[0].token

        # Making Data
        data["facebook"] = []
        data["instagram"] = []
        data['linkedin'] = []
        for _ in social:
            # For Faceboook
            if _.provider == 'facebook':

                page_data = facebook_page_data(access_token.get(_.user.username).get("facebook"),access_token[_.user.username]['id'])
                data["facebook"] += page_data
                insta_data = get_instagram_user_data(access_token.get(_.user.username).get("facebook"),access_token[_.user.username]['id'])
                data["instagram"] += insta_data
            # For Instagram

            if _.provider == 'linkedin_oauth2':

                linkedin_page = linkedin_get_user_organization(access_token.get(_.user.username).get("linkedin_oauth2"),access_token[_.user.username]['id'])
                data['linkedin'] += linkedin_page

        self.request.session['context'] = data



        return JsonResponse(data)


class PostDraftView(UpdateView):
    model = PostModel
    form_class = PostModelForm
    template_name = 'social/publish_drafts.html'
    success_url = reverse_lazy('my_posts')

    def dispatch(self, request, *args, **kwargs):
        user = self.request.user

        if user.is_superuser:
            return redirect(reverse_lazy("my_user"))

        return super(PostDraftView, self).dispatch(request)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post_id = self.kwargs['pk']
        post = PostModel.objects.get(pk=post_id)
        comment_check = post.comment_check
        context = {'form': self.get_form(), 'post': post, 'comment_check': comment_check}
        # context = {'form': self.get_form(), 'comment_check': comment_check}
        return context

    def form_invalid(self, form):
        return redirect(reverse("my_posts", kwargs={'pk': self.request.user.id}))

    def form_valid(self, form):
        requestdata = dict(self.request.POST)

        linkedin_errors = linkedin_validator(self.request)
        facebook_errors = facebook_validator(self.request)
        instagram_errors = instagram_validator(self.request)

        if facebook_errors or instagram_errors or linkedin_errors:
            for errors in facebook_errors:
                messages.error(self.request, facebook_errors[errors])

            for errors in instagram_errors:
                messages.error(self.request, instagram_errors[errors])

            for errors in linkedin_errors:
                messages.error(self.request, linkedin_errors[errors])

            return self.form_invalid(form)

        context = self.request.session.get('context')
        post_id = self.kwargs.get('pk')
        post = PostModel.objects.get(pk=post_id)
        requestdata.pop("csrfmiddlewaretoken")
        caption = requestdata.pop("post")
        post.post = caption[0]
        comment_check = form.cleaned_data.get('comment_check')
        if comment_check:
            post.comment_check = True
        else:
            post.comment_check = False
        action = self.request.POST.get('action', '')
        if action == 'publish':
            post.status = 'PROCESSING'
            post.publish_check = True
        elif action == 'schedule':
            post.status = 'SCHEDULED'
            post.publish_check = False
            schedule_date = self.request.POST.get('date')
            schedule_time = self.request.POST.get('time')
            schedule_datetime_str = f"{schedule_date} {schedule_time}"

            if schedule_datetime_str:
                schedule_datetime = datetime.strptime(schedule_datetime_str, '%Y-%m-%d %H:%M')
                post.schedule_datetime = schedule_datetime

        else:
                post.status == 'DRAFT'
                post.publish_check = False
        post.prepost_page.clear()
        share_pages = []
        if requestdata.get("linkedin") or requestdata.get('facebook') or requestdata.get('instagram'):
            for page in requestdata.get("linkedin") or []:
                i = 0
                while context.get('linkedin')[i]['id'] != page:
                    i += 1
                info = context.get('linkedin').pop(i)
                user = User.objects.get(id=info['user'])
                share_page, created = SharePage.objects.get_or_create(org_id=page, provider='linkedin', user=user,
                                                                      name=info['name'])

                if created:
                    share_page.access_token = SocialToken.objects.get(account__user__id=info['user'],
                                                                      app__provider="linkedin_oauth2").token
                    share_page.save()
                share_pages.append(share_page)

            for page in requestdata.get("facebook") or []:
                i = 0
                while context.get('facebook')[i].get('id') != page:
                    i += 1

                info = context.get('facebook').pop(i)

                ispageexist = SharePage.objects.filter(org_id=info.get('id')).exists()

                if ispageexist:
                    sharepage = SharePage.objects.get(org_id=info.get('id'))
                    share_pages.append(sharepage)

                else:
                    user = User.objects.get(id=info['user'])
                    sharepage = SharePage.objects.create(user=user)
                    sharepage.name = info.get('name')
                    sharepage.access_token = info.get('access_token')
                    sharepage.org_id = info.get('id')
                    sharepage.provider = "facebook"
                    sharepage.save()

                    share_pages.append(sharepage)
            for page in requestdata.get("instagram") or []:
                i = 0
                while context.get('instagram')[i].get('id') != page:
                    i += 1

                info = context.get('instagram').pop(i)
                ispageexist = SharePage.objects.filter(org_id=info.get('id')).exists()
                # Store Shared Page
                if ispageexist:
                    sharepage = SharePage.objects.get(org_id=info.get('id'))
                    share_pages.append(sharepage)

                else:
                    user = User.objects.get(id=info['user'])
                    sharepage = SharePage.objects.create(user=user)
                    sharepage.name = info.get('name')
                    sharepage.access_token = SocialToken.objects.get(account__user__id=info['user'],
                                                                     app__provider="facebook").token
                    sharepage.org_id = info.get('id')
                    sharepage.provider = "instagram"
                    sharepage.save()
                    share_pages.append(sharepage)

        else:
            from django.http import Http404
            raise Http404("Please Select a Page To Share")
        images = self.request.FILES.getlist('images')
        post.save()
        image_object = []
        if images:
            for image in images:
                image_model = ImageModel(image=image)
                image_model.save()
                image_object.append(image_model)
        post.images.add(*image_object)

        post.prepost_page.add(*share_pages)

        return redirect(reverse("my_posts", kwargs={'pk': self.request.user.id}))

def get_paginated_post_list(post_queryset, items_per_page, page_number):
    post = post_queryset.order_by('-created_at')
    paginator = Paginator(post, items_per_page)
    page_obj = paginator.get_page(page_number)


    return page_obj


class PostsGetView2(LoginRequiredMixin, TemplateView):
    template_name = 'social/my_posts2.html'

    def dispatch(self, request, *args, **kwargs):
        user = self.request.user

        if user.is_superuser:
            return redirect(reverse_lazy("my_user"))

        return super(PostsGetView2, self).dispatch(request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_manager = self.request.user.manager

        if user_manager != None:
            role = InviteEmploye.objects.get(selected_user=self.request.user, invited_by=self.request.user.manager)
            user_permission = role.permission
            if user_permission == 'HIDE':
                posts = PostModel.objects.filter(user=self.request.user, is_deleted=False)
            else:
                posts = PostModel.objects.filter(Q(user=self.request.user) | Q(user=self.request.user.manager),
                                                 is_deleted=False)

        else:
            invited = InviteEmploye.objects.filter(invited_by=self.request.user, status="ACCEPTED")
            invites = []
            for user in invited:
                invited_users_id = user.selected_user.id
                invites.append(invited_users_id)
            posts = PostModel.objects.filter(Q(user=self.request.user.id) | Q(user__in=invites), is_deleted=False)


        items_per_page = 6
        search = self.request.GET.get('search', '')
        platform = self.request.GET.get('platform', 'fb')
        platform = 'fb'
        page = self.request.GET.get('page', '1')

        if platform == 'fb' and len(posts.filter(prepost_page__provider="facebook")) > 0:
            facebook_post = posts.filter(prepost_page__provider="facebook").distinct()
            if search is not None and search != '':
                facebook_post = facebook_post.filter(
                    Q(post__icontains=search) | Q(created_at__icontains=search) | Q(status__icontains=search) |
                    Q(user__username__icontains=search) | Q(prepost_page__name__icontains=search))
            paginated = get_paginated_post_list(facebook_post, items_per_page, page)
            # has_facebook_post = any(
            #     any(post_urn.org.provider.name == 'facebook' for post_urn in post.post_urn.all())
            #     for post in paginated
            # )

        else:
            paginated = ''

        context = {
            'platform': platform,
            'paginated': paginated,
        }
        return context


class PostsGetView(LoginRequiredMixin, TemplateView):
    template_name = 'social/my_posts.html'

    def dispatch(self, request, *args, **kwargs):
        user = self.request.user

        if user.is_superuser:
            return redirect(reverse_lazy("my_user"))

        return super(PostsGetView, self).dispatch(request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_manager = self.request.user.manager

        if user_manager != None:
            role = InviteEmploye.objects.get(selected_user=self.request.user, invited_by=self.request.user.manager)
            user_permission = role.permission
            if user_permission == 'HIDE':
                posts = PostModel.objects.filter(user=self.request.user, is_deleted=False)
            else:
                posts = PostModel.objects.filter(Q(user=self.request.user) | Q(user=self.request.user.manager), is_deleted=False)

        else:
            invited = InviteEmploye.objects.filter(invited_by=self.request.user, status="ACCEPTED")
            invites = []
            for user in invited:
                invited_users_id = user.selected_user.id
                invites.append(invited_users_id)
            posts = PostModel.objects.filter(Q(user=self.request.user.id) | Q(user__in=invites), is_deleted=False)

        items_per_page = 2
        search = self.request.GET.get('search', '')
        platform = self.request.GET.get('platform', 'fb')
        # platform = 'fb'
        page = self.request.GET.get('page', '1')



        if platform =='ln' and len(posts.filter(prepost_page__provider="linkedin")) > 0:
            linkedin_post = posts.filter(prepost_page__provider="linkedin").distinct()
            if search is not None and search != '':
                linkedin_post = linkedin_post.filter(
                    Q(post__icontains=search) | Q(created_at__icontains=search) | Q(status__icontains=search) |
                    Q(user__username__icontains=search) | Q(prepost_page__name__icontains=search))
            linkedin_post_paginated = get_paginated_post_list(linkedin_post, items_per_page, page)
        else:
            linkedin_post_paginated = ''


        if platform == 'fb' and len(posts.filter(prepost_page__provider="facebook")) > 0:
            facebook_post = posts.filter(prepost_page__provider="facebook").distinct()
            if search is not None and search != '':
                facebook_post = facebook_post.filter(
                    Q(post__icontains=search) | Q(created_at__icontains=search) | Q(status__icontains=search) |
                    Q(user__username__icontains=search) | Q(prepost_page__name__icontains=search))
            facebook_post_paginated = get_paginated_post_list(facebook_post, items_per_page, page)
        else:

            facebook_post_paginated = ''


        if platform == 'insta' and len(posts.filter(prepost_page__provider="instagram")) > 0:
            instagram_post = posts.filter(prepost_page__provider="instagram").distinct()
            if search is not None and search != '':
                instagram_post = instagram_post.filter(
                    Q(post__icontains=search) | Q(created_at__icontains=search) | Q(status__icontains=search) |
                    Q(user__username__icontains=search) | Q(prepost_page__name__icontains=search))
            instagram_post_paginated = get_paginated_post_list(instagram_post, items_per_page, page)
        else:

            instagram_post_paginated = ''

        if platform == 'google' and len(posts.filter(prepost_page__provider="Google Books")) > 0:
            google_post = posts.filter(prepost_page__provider="Google Books").distinct()
            if search is not None and search != '':
                google_post = google_post.filter(
                    Q(post__icontains=search) | Q(created_at__icontains=search) | Q(status__icontains=search) |
                    Q(user__username__icontains=search) | Q(prepost_page__name__icontains=search))
            google_post_paginated = get_paginated_post_list(google_post, items_per_page, page)

        else:
            google_post_paginated = ''


        context = {
            'platform': platform,
            # 'paginated': paginated,
            'linkedin_post': linkedin_post_paginated,
            'facebook_post': facebook_post_paginated,
            'instagram_post': instagram_post_paginated,
            'google_post': google_post_paginated,
            # 'paginated': paginated,
            # 'posts': PostModel.objects.filter(user_id=self.request.user.id),
        }
        return context



class PostApiView(ListAPIView):
    serializer_class = PostSerializer
    pagination_class = LinkHeaderPagination


    def get_queryset(self):
        user_manager = self.request.user.manager

        if user_manager != None:
            role = InviteEmploye.objects.get(selected_user=self.request.user, invited_by=self.request.user.manager)
            user_permission = role.permission
            if user_permission == 'HIDE':
                posts = PostModel.objects.filter(user=self.request.user, is_deleted=False)
            else:
                posts = PostModel.objects.filter(Q(user=self.request.user) | Q(user=self.request.user.manager),
                                                 is_deleted=False)

        else:
            invited = InviteEmploye.objects.filter(invited_by=self.request.user, status="ACCEPTED")
            invites = []
            for user in invited:
                invited_users_id = user.selected_user.id
                invites.append(invited_users_id)
            posts = PostModel.objects.filter(Q(user=self.request.user.id) | Q(user__in=invites), is_deleted=False)



        search = self.request.GET.get('search', '')
        platform = self.request.GET.get('platform', 'fb')
        page = self.request.GET.get('page', '1')

        if platform == 'ln' and len(posts.filter(prepost_page__provider="linkedin")) > 0:
            post = posts.filter(prepost_page__provider="linkedin").distinct()


            if search is not None and search != '':
                post = post.filter(
                    Q(post__icontains=search) | Q(created_at__icontains=search) | Q(status__icontains=search) |
                    Q(user__username__icontains=search) | Q(prepost_page__name__icontains=search))
            post = post.order_by('-created_at')

        elif platform == 'fb' and len(posts.filter(prepost_page__provider="facebook")) > 0:
            post = posts.filter(prepost_page__provider="facebook").distinct()
            if search is not None and search != '':
                post = post.filter(
                    Q(post__icontains=search) | Q(created_at__icontains=search) | Q(status__icontains=search) |
                    Q(user__username__icontains=search) | Q(prepost_page__name__icontains=search))
            post = post.order_by('-created_at')

        elif platform == 'insta' and len(posts.filter(prepost_page__provider="instagram")) > 0:
            post = posts.filter(prepost_page__provider="instagram").distinct()
            if search is not None and search != '':
                post = post.filter(
                    Q(post__icontains=search) | Q(created_at__icontains=search) | Q(status__icontains=search) |
                    Q(user__username__icontains=search) | Q(prepost_page__name__icontains=search))
            post = post.order_by('-created_at')

        elif platform == 'google' and len(posts.filter(prepost_page__provider="Google Books")) > 0:
            post = posts.filter(prepost_page__provider="Google Books").distinct()
            if search is not None and search != '':
                post = post.filter(
                    Q(post__icontains=search) | Q(created_at__icontains=search) | Q(status__icontains=search) |
                    Q(user__username__icontains=search) | Q(prepost_page__name__icontains=search))
            post = post.order_by('-created_at')
        else:
            post = []

        return post

    # def get_page_number(self, request, paginator):
    #     page_number = request.query_params.get(self.page_query_param, 1)
    #     if page_number in self.last_page_strings:
    #         page_number = paginator.num_pages
    #     return page_number
    #
    # def get_paginated_response(self, post):
    #     return Response(OrderedDict([
    #         ('count', self.page.paginator.count),
    #         ('next', self.get_next_link()),
    #         ('previous', self.get_previous_link()),
    #         ('results', data)
    #     ]))




class PostDeleteView(DestroyAPIView):
    queryset = PostModel.objects.all()
    serializer_class = PostImageSerializer
    def delete(self, request, *args, **kwargs):
        page_id = self.request.GET.get('page_id')
        comment_urn = self.request.GET.get('urn')
        actor = self.request.GET.get('actor')
        comment_id = self.request.GET.get('comment_id')

        page_name = self.request.GET.get('page_name')
        response = {}
        response['user'] = self.request.user.id
        post = self.get_object()
        if self.request.GET.get('page_name') == "facebook" or page_name == 'facebook':
            try:
                post_urn = post.post_urn.all().filter(pk=page_id).first()
                if post_urn is None and (comment_urn == '' or comment_urn is None):
                    post_urn1 = post.post_urn.all().filter(org__provider='facebook')

                    if len(post_urn1) > 0:
                        for urn1 in post_urn1:
                            access_token = urn1.org.access_token
                            urn = urn1.urn
                            page = urn1.org.id
                            response['message'] = delete_meta_posts_comment(access_token, urn)
                            response['request'] = "post"

                            if response['message'] == 'success':
                                post.post_urn.remove(urn1)
                                urn1.is_deleted = True
                                urn1.save()
                                post.prepost_page.remove(page)
                                prepost = post.prepost_page.all().filter(provider='facebook')
                                for page in prepost:
                                    post.prepost_page.remove(page)
                                if len(post.post_urn.all()) == 0:
                                    post.delete()
                    else:
                        prepost = post.prepost_page.all().filter(provider='facebook')
                        for page in prepost:
                            post.prepost_page.remove(page)
                            if len(post.prepost_page.all()) == 0:
                                post.delete()
                else:

                    access_token = post_urn.org.access_token
                    urn = post_urn.urn
                    page = Post_urn.objects.get(id = page_id).org

                    if comment_urn:
                        response['message'] = delete_meta_posts_comment(access_token, comment_urn)
                        response['request'] = "comment"
                    else:
                        response['message'] = delete_meta_posts_comment(access_token, urn)
                        response['request'] = "post"

                        if response['message'] == 'success':
                            post.post_urn.remove(post_urn)
                            post.prepost_page.remove(page)
                            post_urn.is_deleted = True
                            post_urn.save()
                            if len(post.post_urn.all()) == 0:
                                post.delete()

            except Exception as e:
                return JsonResponse('failed',e)

        elif self.request.GET.get('page_name') == "instagram" or page_name == 'instagram':
            try:


                page_post = post.post_urn.all().filter(pk=page_id).first()
                if page_post is None and (comment_urn == '' or comment_urn is None):
                    prepost = post.prepost_page.all().filter(provider='instagram')
                    for page in prepost:
                        post.prepost_page.remove(page)
                        if len(post.prepost_page.all()) == 0:
                            post.delete()
                else:
                    access_token = page_post.org.access_token
                    urn = page_post.urn

                    if comment_urn:
                        response['message'] = delete_meta_posts_comment(access_token, comment_urn)
                        response['request'] = 'comment'

            except Exception as e:
                return 'failed'
        elif self.request.GET.get('page_name') == "linkedin" or page_name == 'linkedin':
            try:
                page_post = post.post_urn.all().filter(pk=page_id).first()
                if page_post is None and (comment_urn == '' or comment_urn is None):
                    post_urn1 = post.post_urn.all().filter(org__provider='linkedin')
                    if len(post_urn1) > 0:
                        for urn1 in post_urn1:
                            post_urn = urn1.urn
                            access_token = urn1.org.access_token

                            response['message'] = delete_linkedin_posts(access_token, post_urn)
                            response['request'] = 'post'

                            if response['message'] == 'success':
                                post.post_urn.remove(urn1)
                                urn1.is_deleted = True
                                urn1.save()
                                prepost = post.prepost_page.all().filter(provider='linkedin')
                                for page in prepost:
                                    post.prepost_page.remove(page)
                                if len(post.post_urn.all()) == 0:
                                    post.delete()
                    else:
                        prepost = post.prepost_page.all().filter(provider='linkedin')
                        for page in prepost:
                            post.prepost_page.remove(page)
                            if len(post.prepost_page.all()) == 0:
                                post.delete()
                else:
                    post_urn = page_post.urn
                    page = Post_urn.objects.get(id = page_id).org
                    access_token = page_post.org.access_token

                    if comment_urn:
                        response['message'] = delete_linkedin_comments(access_token, post_urn, comment_id, actor)
                        response['request'] = 'comment'
                    else:
                        response['message'] = delete_linkedin_posts(access_token, post_urn)
                        response['request'] = 'post'

                        if response['message'] == 'success':
                            post.post_urn.remove(page_post)
                            post.prepost_page.remove(page)
                            page_post.is_deleted = True
                            page_post.save()

                            if len(post.post_urn.all()) == 0:
                                post.delete()

            except Exception as e:
                return 'failed'

        return JsonResponse(response)




class PostsDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'social/post_detail.html'

    def dispatch(self, request, *args, **kwargs):
        user = self.request.user

        if user.is_superuser:
            return redirect(reverse_lazy("my_user"))

        return super(PostsDetailView, self).dispatch(request)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post_id = self.kwargs['post_id']
        page_id = self.kwargs['page_id']


        posted_on = Post_urn.objects.get(id=page_id).org.name
        name = self.request.GET.get('page_name')


        if self.request.GET.get('page_name') == 'linkedin':

            provider_name = "linkedin"
            linkedin_post = PostModel.objects.get(post_urn__org__provider=provider_name, id=post_id, post_urn__pk=page_id)
            # social = SocialAccount.objects.get(user=linkedin_post.user.id, provider='linkedin_oauth2')

            org_id = linkedin_post.post_urn.all().filter(pk=page_id).first().org.org_id
            post_urn = linkedin_post.post_urn.all().filter(pk=page_id).first().urn
            is_liked = linkedin_post.post_urn.all().filter(pk=page_id).first().is_liked

            # my eddited
            access_token_string = linkedin_post.post_urn.all().filter(pk=page_id).first().org.access_token

            urn = post_urn
            if urn == '' or urn == None:
                    pass
            else:
                    prefix, value = post_urn.rsplit(':', 1)
                    if prefix == 'urn:li:ugcPost':
                        result = ugcpost_socialactions(urn, access_token_string, linkedin_post)
                        no_likes = result[0]
                        no_comments = result[1]
                        data = result[2]
                        next = result[3]

                    else:
                        result = linkedin_post_socialactions(urn, access_token_string, linkedin_post)
                        no_likes = result[0]
                        no_comments = result[1]
                        data = result[2]
                        next = result[3]


            context = {
                'ids': urn,
                'no_likes': no_likes,
                'no_comments': no_comments,
                'data': data,
                'next': next,
                'posts': PostModel.objects.filter(user_id=self.request.user.id),
                'post': linkedin_post,
                'posted_on': posted_on,
                'post_id': post_id,
                'page_id': page_id,
                'provider_name': provider_name,
                'is_liked': is_liked
            }

        elif self.request.GET.get('page_name') == 'facebook':
            provider_name = "facebook"

            facebook_post = PostModel.objects.get(post_urn__org__provider=provider_name, id=post_id,post_urn__pk=page_id)
            org_id = facebook_post.post_urn.all().filter(pk=page_id).first().org.org_id
            post_urn = facebook_post.post_urn.all().filter(pk = page_id).first().urn
            is_liked = facebook_post.post_urn.all().filter(pk = page_id).first().is_liked
            access_token_string = facebook_post.post_urn.all().filter(pk=page_id).first().org.access_token
            urn = post_urn
            if urn == '' or urn == None:
                pass
            else:
                result = fb_socialactions(urn, access_token_string,org_id)
                no_likes = result[0]
                no_comments = result[1]
                data = result[2]
                picture_url = result[3]
                next = result[4]

            context = {
                'ids': urn,
                'no_likes': no_likes,
                'is_liked': is_liked,
                'no_comments': no_comments,
                'data': data,
                'next': next,
                'picture_url':picture_url,
                'posts': PostModel.objects.filter(user_id=self.request.user.id),
                'post': facebook_post,
                'posted_on': posted_on,
                'post_id': post_id,
                'page_id': page_id,
                'provider_name': provider_name,
                'reply_media_counter': 0
            }
        elif self.request.GET.get('page_name') == 'instagram':
            provider_name = "instagram"
            instagram_post = PostModel.objects.get(post_urn__org__provider=provider_name, id=post_id, post_urn__pk=page_id)
            user = instagram_post.user
            org_id = instagram_post.post_urn.all().filter(pk=page_id).first().org.org_id
            post_urn = instagram_post.post_urn.all().filter(pk=page_id).first().urn
            access_token = instagram_post.post_urn.all().filter(pk=page_id).first().org.access_token
            urn = post_urn

            if urn == '' or urn == None:
                pass
            else:

                result = insta_socialactions(urn, access_token,org_id)
                no_likes = result[0]
                no_comments = result[1]
                data = result[2]
                picture_url = result[3]
                next = result[4]


            context = {
                'ids': urn,
                'no_likes': no_likes,
                'no_comments': no_comments,
                'data': data,
                'next':next,
                 'picture_url':picture_url,
                'posts': PostModel.objects.filter(user_id=self.request.user.id),
                'post': instagram_post,
                'posted_on': posted_on,
                'post_id': post_id,
                'page_id': page_id,
                'provider_name': provider_name,
                'reply_media_counter': 0
            }


        return context

    from django.views.decorators.http import require_http_methods

    @require_http_methods(['DELETE'])
    def delete_post(request, pk):
        # remove the film from the user's list
        request.user.file.remove(pk)

        # return the template fragment
        file = request.user.file.all()
        return render(request, 'publish_drafts.html', {'posts': file})

    def post(self, request, **kwargs):
        comment = self.request.POST.get('comment')
        comment_urn_list = request.POST.getlist('comment_urn')
        user_id_list = request.POST.getlist('user_id')
        media = request.FILES.get('comment_media')
        post_id = self.kwargs['post_id']
        page_id = self.kwargs['page_id']

        reply_list = request.POST.getlist('reply')
        reply_data = {}
        reply_media_counter = 1
        for comment_urn, reply,user_id in zip(comment_urn_list, reply_list,user_id_list):
            reply_data[comment_urn] = [reply]
            reply_media = request.FILES.get(f"reply_media_{reply_media_counter}")
            reply_data[comment_urn].append(reply_media)
            reply_data[comment_urn].append(user_id)
            reply_media_counter = reply_media_counter+1


        if comment != ''  or media != None and len(reply_list) == 0:
            if self.request.GET.get('page_name') == 'linkedin':
                provider_name = "linkedin"
                linkedin_post = PostModel.objects.get(post_urn__org__provider=provider_name, id=post_id,post_urn__pk=page_id)

                org_id = linkedin_post.post_urn.all().filter(pk=page_id).first().org.org_id
                post_urn = linkedin_post.post_urn.all().filter(pk=page_id).first()
                access_token = post_urn.org.access_token
                user = post_urn.org.user
                social = SocialAccount.objects.get(user=user.id, provider='linkedin_oauth2')
                post_urn = post_urn.urn

                # result = linkedin_retrieve_access_token(post_id)
                #
                # access_token = result[1]
                # social = result[3]
                # if comment != '' and media == None:
                if comment != '' or comment != None:
                    create_comment(access_token, post_urn, comment, social)
                # elif media != '':
                #     # create_comment_media_linkedin(org_id, access_token, post_urn, comment, social, media)
                #     image_comment(org_id, access_token, post_urn, comment, social, media)


            elif self.request.GET.get('page_name') == 'facebook':
                provider_name = "facebook"
                facebook_post = PostModel.objects.get(post_urn__org__provider = provider_name,id = post_id,post_urn__pk = page_id)
                post_urn = facebook_post.post_urn.all().filter(pk = page_id).first()

                access_token = post_urn.org.access_token

                urn = post_urn.urn

                result = meta_comments(urn, comment, media, access_token)

            elif self.request.GET.get('page_name') == 'instagram':
                provider_name = "instagram"
                instagram_post = PostModel.objects.get(post_urn__org__provider = provider_name,id = post_id, post_urn__pk = page_id)
                post_urn = instagram_post.post_urn.all().filter(pk = page_id).first()
                # facebook_account = SocialAccount.objects.get(user_id=self.request.user.id, provider="facebook")
                access_token = post_urn.org.access_token
                text = instagram_post.post
                urn = post_urn.urn


                result = meta_comments(urn ,comment ,media,access_token) # but it dose not support images and videos




            return redirect(reverse("my_detail_posts", kwargs={'post_id': post_id, 'page_id': page_id}) + f'?page_name={self.request.GET.get("page_name")}')

        elif len(reply_list) > 0:
            if self.request.GET.get('page_name') == 'linkedin':
                provider_name = "linkedin"
                linkedin_post = PostModel.objects.get(post_urn__org__provider=provider_name, id=post_id,post_urn__pk=page_id)
                org_id = linkedin_post.post_urn.all().filter(pk=page_id).first().org.org_id

                post_urn = linkedin_post.post_urn.all().filter(pk=page_id).first()
                access_token = post_urn.org.access_token
                user = post_urn.org.user
                social = SocialAccount.objects.get(user=user.id, provider='linkedin_oauth2')
                post_urn = post_urn.urn

                # result = linkedin_retrieve_access_token(post_id)
                # access_token = result[1]
                # social = result[3]
                for comment_urn, reply in reply_data.items():
                    # if reply[0] != '' and reply[1] is None:
                    if reply[0] != '':
                        result = post_nested_comment_linkedin(social, access_token, post_urn, reply[0], comment_urn)
                    else:
                        pass
                    # elif reply[0] == '' and media is None:
                    #     pass
                    # else:
                    #     media = reply[1]
                    #     result = post_nested_comment_media_linkedin(social,access_token,post_urn,reply[0],comment_urn, media,org_id)
            elif self.request.GET.get('page_name') == 'facebook':


                # message = reply_data[0]
                # message_split = message.split(" ")
                # for x in range(len(message_split)):
                #     if "@" in message_split[x]:
                #         element = message_split[x]
                #         newelement = f"@[{{{reply[2]}}}]"
                #         message_split[x] = newelement
                #
                # message = message.join(" ")
                # reply_data[0] = message


                provider_name = "facebook"
                facebook_post = PostModel.objects.get(post_urn__org__provider=provider_name, id=post_id,
                                                      post_urn__pk=page_id)

                post_urn = facebook_post.post_urn.all().filter(pk=page_id).first()

                access_token = post_urn.org.access_token
                for comment_urn, reply in reply_data.items():

                    message = reply[0]
                    message_split = message.split(" ")
                    for x in range(len(message_split)):
                        if "@" in message_split[x]:
                            element = message_split[x]
                            newelement = f"@[{reply[2]}]"
                            message_split[x] = newelement

                    message = " ".join(message_split)
                    reply[0] = message
                    if reply[0] != '' or reply[1]!=None:
                        result = meta_nested_comment(comment_urn, reply[0], reply[1], access_token, provider_name)
                    else:
                        pass
            else:
                provider_name = "instagram"
                instagram_post = PostModel.objects.get(post_urn__org__provider=provider_name, id=post_id,
                                                      post_urn__pk=page_id)
                post_urn = instagram_post.post_urn.all().filter(pk=page_id).first()

                access_token = post_urn.org.access_token
                for comment_urn, reply in reply_data.items():
                    if reply[0] != '':
                        result = meta_nested_comment(comment_urn, reply[0], reply[1], access_token, provider_name)
                    else:
                        pass

            return redirect(reverse("my_detail_posts", kwargs={'post_id': post_id, 'page_id': page_id}) + f'?page_name={self.request.GET.get("page_name")}')
        # elif post_like:
        #     if self.request.GET.get('page_name') == 'linkedin':
        #         provider_name = "linkedin"
        #         linkedin_post = PostModel.objects.get(post_urn__org__provider=provider_name, id=post_id, post_urn__pk=page_id)
        #         user = linkedin_post.user
        #         post_urn = linkedin_post.post_urn.all().filter(pk=page_id).first().urn
        #         result = linkedin_retrieve_access_token(post_id)
        #
        #         access_token = result[1]
        #         social = result[3]
        #         result = post_like_linkedin(post_urn, user, access_token)
        else:
            pass

        return redirect(reverse("my_detail_posts", kwargs={'post_id': post_id, 'page_id': page_id}))

class CommentPostApi(APIView):

    def post(self,request,**kwargs):
        comment = self.request.data.get('text')
        post_id = self.kwargs['post_id']
        page_id = self.kwargs['page_id']
        provider_name = self.request.GET.get('page_name')
        data = dict()
        if not comment:
            return JsonResponse({'message': 'Comment text is required.'}, status=400)

        try:
            post = PostModel.objects.get(
                post_urn__org__provider=provider_name,
                id=post_id,
                post_urn__pk=page_id
            )
            post_urn = post.post_urn.all().filter(pk=page_id).first()
            access_token = post_urn.org.access_token
            user = post_urn.org.user
            post_urn = post_urn.urn
            result = "error"
            if provider_name == "linkedin":
                social = SocialAccount.objects.get(user=user.id, provider='linkedin_oauth2')
                result = create_comment(access_token, post_urn, comment, social)
            elif provider_name == 'facebook':
                media = None
                result = meta_comments(post_urn, comment, media, access_token,provider_name)
            elif provider_name == 'instagram':
                media = None
                result = meta_comments(post_urn, comment, media, access_token,provider_name)

            if result == "error":
                raise "Falied To Post Reply"

            return JsonResponse({'comment_response': result})


        except PostModel.DoesNotExist:

            raise NotFound('Post not found for the specified parameters.')


        except SocialAccount.DoesNotExist:

            raise NotFound('Social Account not found for the specified user.')


        except Exception as e:

            return JsonResponse({'message': str(e)}, status=500)


class ReplyPostApi(APIView):

    def post(self,request,**kwargs):
        comment = self.request.data.get('text')
        comment_urn = self.request.data.get('urn')
        post_id = self.kwargs['post_id']
        page_id = self.kwargs['page_id']
        provider_name = self.request.GET.get('page_name')
        data = dict()
        if not comment:
            return JsonResponse({'message': 'Comment text is required.'}, status=400)

        try:
            post = PostModel.objects.get(
                post_urn__org__provider=provider_name,
                id=post_id,
                post_urn__pk=page_id
            )
            post_urn = post.post_urn.all().filter(pk=page_id).first()
            access_token = post_urn.org.access_token
            user = post_urn.org.user
            post_urn = post_urn.urn
            result = "error"
            if provider_name == "linkedin":
                social = SocialAccount.objects.get(user=user.id, provider='linkedin_oauth2')
                result = result = post_nested_comment_linkedin(social, access_token, post_urn, comment, comment_urn)
            elif provider_name == 'facebook':
                media = None
                result = meta_nested_comment(comment_urn,comment,media,access_token, provider_name)
            elif provider_name == 'instagram':
                media = None
                result = meta_nested_comment(comment_urn,comment,media,access_token, provider_name)

            if result == "error":
                raise "Falied To Post Comment"

            return JsonResponse({'comment_response': result})


        except PostModel.DoesNotExist:

            raise NotFound('Post not found for the specified parameters.')


        except SocialAccount.DoesNotExist:

            raise NotFound('Social Account not found for the specified user.')


        except Exception as e:

            return JsonResponse({'message': str(e)}, status=500)

class ReplyPagination(APIView):

    def get(self,request,**kwargs):
        pagination = self.request.GET.get("pagination_link")
        post_id = self.kwargs['post_id']
        page_id = self.kwargs['page_id']
        provider_name = self.request.GET.get('page_name')
        data = dict()


        try:

            access_token = Post_urn.objects.filter(id = page_id).first().org.access_token
            result = "error"
            if provider_name == "linkedin":
                # social = SocialAccount.objects.get(user=user.id, provider='linkedin_oauth2')
                result = linkdein_pagination(pagination,access_token,"reply")
            elif provider_name == 'facebook':

                result = meta_reply_pagination(pagination, access_token, provider_name)
            elif provider_name == 'instagram':
                result = result = meta_reply_pagination(pagination, access_token, provider_name)

            if result == "error":
                raise "Failed to fetch replies"

            return JsonResponse(result,safe=False)


        except PostModel.DoesNotExist:

            raise NotFound('Post not found for the specified parameters.')


        except SocialAccount.DoesNotExist:

            raise NotFound('Social Account not found for the specified user.')


        except Exception as e:

            return JsonResponse({'message': str(e)}, status=400)
class CommentPagination(APIView):

    def get(self,request,**kwargs):
        pagination = self.request.GET.get("pagination_link")
        post_id = self.kwargs['post_id']
        page_id = self.kwargs['page_id']
        provider_name = self.request.GET.get('page_name')
        data = dict()


        try:

            access_token = Post_urn.objects.filter(id = page_id).first().org.access_token
            result = "error"
            if provider_name == "linkedin":

               result = linkdein_pagination(pagination,access_token,"comment")
            elif provider_name == 'facebook':

                result = meta_reply_pagination(pagination, access_token, provider_name)
            elif provider_name == 'instagram':
                result = meta_reply_pagination(pagination, access_token, provider_name)

            if result == "error":
                raise "Failed to fetch replies"

            return JsonResponse(result,safe=False)


        except SharePage.DoesNotExist:

            raise NotFound('Post not found for the specified parameters.')


        except Exception as e:

            return JsonResponse({'message': str(e)}, status=400)



class BusinessView(TemplateView):
    template_name = 'socialaccount/business_profile.html'




class ConnectionView(ConnectionsView):

    def get_context_data(self, **kwargs):
        context = super(ConnectionView, self).get_context_data()

        from allauth.socialaccount.models import SocialApp

        social_apps = SocialApp.objects.all()
        referrer = self.request.META.get('HTTP_REFERER', '')
        for apps in social_apps:
            context[f'{apps.provider}_app'] = apps
            try:
                context[f'{apps.provider}'] = SocialAccount.objects.filter(user=self.request.user.id, provider=apps.provider).first()


            except Exception as e:
                e

        if referrer == "" and context.get('instagram') and not context.get('facebook'):
            context['error'] = True

        elif referrer != "" and context.get('instagram') and not context.get('facebook'):
            context['error'] = True

        return context




class SocialProfileView(LoginRequiredMixin,TemplateView):
    template_name = 'social/social_profile_2.html'

    def dispatch(self, request, *args, **kwargs):
        user = self.request.user

        if user.is_superuser:
            return redirect(reverse_lazy("my_user"))

        return super(SocialProfileView, self).dispatch(request)

    def get_context_data(self, **kwargs):
        provider_name = self.request.GET.get('provider_name')
        providertoGetdetails = self.request.GET.get('provider_name')
        user = self.request.user

        if provider_name == "instagram":
            provider_name = "facebook"

        user_manager = self.request.user.manager

        if user_manager:
            selected_user = InviteEmploye.objects.get(selected_user=self.request.user,
                                                      invited_by=self.request.user.manager, status ='ACCEPTED')
            role = selected_user.role
            permission = selected_user.permission

            if role == "ADMIN":
                invited_employees_list = InviteEmploye.objects.filter(Q(permission="WRITE") | Q(permission="READ"),
                                                                 invited_by=user, status ='ACCEPTED').values_list('selected_user__id', flat=True)



                social = SocialAccount.objects.filter(Q(user=user.id) | Q(user__in=invited_employees_list) | Q(user=user_manager.id),
                                                      provider=provider_name,user__is_deleted = False)


            elif (role == "MEMBER" and (permission == "READ" or permission == "WRITE")):
                social = SocialAccount.objects.filter(Q(user=user.id) | Q(user=user_manager.id), provider=provider_name,user__is_deleted = False)

            else:
                social = SocialAccount.objects.filter(Q(user=user.id), provider=provider_name,user__is_deleted = False)

        else:
            invited_employees_list = InviteEmploye.objects.filter(Q( permission = "WRITE" ) | Q( permission = "READ" ) , invited_by = user).values_list('selected_user__id', flat=True)




            social = SocialAccount.objects.filter(Q(user=user.id) |Q(user__in=invited_employees_list), provider=provider_name,user__is_deleted = False)

        # This is to sort the social account user with there role ADMIN first then Managers

        condition = Case(
                When(user=user.id, then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            )

        social = social.annotate(user_admin=condition)
        social = social.order_by('-user_admin')



        access_token = {}
        data = dict()

        for _ in social:
                access_token[_.user.id] = SocialToken.objects.filter(account_id=_).first().token


        user_access_token = access_token[user.id]

        if providertoGetdetails == "facebook":
            try:
                data = fb_user_detail(user_access_token)
                if data.get('error') != None:
                    raise Exception(data['error'])

                data['pages'] = {}
                data ['user_roles'] = {}
                for _ in social:
                    responses = facebook_page_data(access_token.get(_.user.id), _.user.id)

                    for response in responses:
                        self.meta_save_share_page(_.user,response,providertoGetdetails)
                        response.pop('access_token')
                    data['pages'][_.user.username] = responses
                    data['user_roles'][_.user.username] = [self.get_user_role(_.user) , _.user.id]

                data['provider'] = "facebook"

            except Exception as e:
                data['error'] = e

        elif providertoGetdetails == "instagram":
            try:
                data['pages'] = {}
                data ['user_roles'] = {}
                for _ in social:
                    accounts = get_instagram_user_data(access_token[_.user.id], _.user.id)
                    instagram__connected_social_account = SocialAccount.objects.get(user=_.user.id, provider="instagram")

                    for account in accounts:
                        self.meta_save_share_page(_.user,account, providertoGetdetails)
                        if account.get('username') == instagram__connected_social_account.extra_data.get('username'):
                               if _.user.id == user.id:
                                    data.update(instagram_details(access_token[_.user.id], account['id']))
                               if data.get("error") != None:
                                    raise Exception(data['error'])
                               data['user_roles'][_.user.username] = [self.get_user_role(_.user), account['id']]

                               if data['pages'].get(_.user.username):
                                  pass
                               else:
                                   data['pages'][_.user.username] = []
                        else:
                            if data['pages'].get(_.user.username):
                                data['pages'][_.user.username].append(account)
                            else:
                                data['pages'][_.user.username] = [account]


                return data
            except Exception as e:
                pass


        elif providertoGetdetails == "linkedin_oauth2":

            try:
                id = social.filter(user = user , provider = "linkedin_oauth2").first().uid
                data = get_linkedin_user_data(user_access_token,id)
                if data.get('error') != None:
                    raise Exception(data['error'])

                data['pages'] = {}
                data['user_roles'] = {}
                for _ in social:
                    responses = linkedin_get_user_organization(access_token.get(_.user.id),_.user.id)

                    for response in responses:
                        self.meta_save_share_page(_.user, response, 'linkedin')
                    data['pages'][_.user.username] = responses
                    data['user_roles'][_.user.username] = [self.get_user_role(_.user), _.user.id]

                data['provider'] = "linkedin"

            except Exception as e:
                data['error'] = e

            return data



        else:
            pass



        context = data
        return context


    def get_user_role(self,user):
        user_manager = user.manager

        if user_manager:
            selected_user = InviteEmploye.objects.filter(selected_user=user,
                                                        invited_by=user_manager, status='ACCEPTED').first()
            role = selected_user.role
            return role


        else:
           return "ADMIN"

    def meta_save_share_page(self,user,object,provider):
        id = object['id']
        name = object['name']

        share_page, created = SharePage.objects.get_or_create(user = user, org_id = id, name = name , provider = provider)

        if created:

            if provider == "facebook":
                share_page.access_token = object['access_token']
            elif provider == "instagram" :
                access_token = SocialToken.objects.get(account__user = user , account__provider = "facebook").token
                share_page.access_token = access_token
            else:
                access_token = SocialToken.objects.get(account__user=user, account__provider="linkedin_oauth2").token
                share_page.access_token = access_token

            share_page.save()


class SocialProfileAPI(APIView):

    def post(self, request):
        provider_name = self.request.GET.get('page_name')
        request_type = self.request.data.get('type')
        id = self.request.data.get('id')
        page_id = self.request.data.get('page_id')
        if provider_name == "facebook":
            if request_type == "account":
                try:
                    access_token = SocialToken.objects.get(
                        account__user__id=id, account__provider=provider_name
                    ).token
                    response = fb_user_detail(access_token)
                    return JsonResponse(response)
                except SocialToken.DoesNotExist:
                    raise NotFound("SocialToken not found for the specified user.")
            elif request_type == "page":
                try:
                    page = SharePage.objects.get(org_id=page_id,user__id = id)
                    access_token = page.access_token
                    org_id = page.org_id

                    response = fb_page_detail(org_id, access_token)
                    return JsonResponse(response)
                except SharePage.DoesNotExist:
                    raise NotFound("SharePage not found for the specified org_id.")
            else:
                return JsonResponse({"error": "Invalid request type."}, status=400)
        elif provider_name == "instagram":
            if request_type == "account":
                try:
                    account = SharePage.objects.filter(org_id=id).first()
                    if not account:
                        raise ObjectDoesNotExist("SharePage not found for the specified org_id.")
                    access_token = account.access_token
                    org_id = account.org_id
                    response = instagram_details(access_token,org_id)
                    return JsonResponse(response)
                except ObjectDoesNotExist:
                    raise NotFound("SharePage not found for the specified org_id.")
            elif request_type == "page":
                try:
                    account = SharePage.objects.filter(org_id=page_id).first()
                    if not account:
                        raise ObjectDoesNotExist("SharePage not found for the specified org_id.")
                    access_token = account.access_token
                    org_id = account.org_id
                    response = instagram_details(access_token,org_id)
                    return JsonResponse(response)
                except ObjectDoesNotExist:
                    raise NotFound("SharePage not found for the specified org_id.")
            else:
                return JsonResponse({"error": "Invalid request type."}, status=400)

        elif provider_name == "linkedin_oauth2":
            if request_type == "account":
                try:
                    access_token = SocialToken.objects.get(
                        account__user__id=id, account__provider=provider_name
                    ).token
                    id = SocialAccount.objects.filter(user__id = id,provider = provider_name).first().uid
                    response = get_linkedin_user_data(access_token,id)
                    return JsonResponse(response)
                except SocialToken.DoesNotExist:
                    raise NotFound("SocialToken not found for the specified user.")
            elif request_type == "page":
                try:

                    page = SharePage.objects.get(org_id=page_id,user__id = id)
                    access_token = page.access_token
                    org_id = page.org_id

                    response = linkedin_page_detail(access_token, org_id)
                    return JsonResponse(response)
                except SharePage.DoesNotExist:
                    raise NotFound("SharePage not found for the specified org_id.")
            else:
                return JsonResponse({"error": "Invalid request type."}, status=400)

        else:
            return JsonResponse({"error": "Invalid provider name."}, status=400)

















class EditUserView(LoginRequiredMixin,UpdateView):
    template_name = 'registration/edituser.html'
    model = User
    form_class = CustomUserUpdateForm
    success_url = reverse_lazy('my_profile')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        user_manager = user.manager

        if user_manager:
            invited_user = InviteEmploye.objects.filter(selected_user=user , invited_by= user_manager).first()
            role = invited_user.role
            context['user_role'] = role

        else:
            context['user_role'] = "ADMIN"

        return context



    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs['request'] = self.request
        return kwargs

    def form_invalid(self, form):
        invalid_form = super(EditUserView,self).form_invalid((form))

        # To use the current user data in context otherwise the form will send user
        # in context with form data
        # for example if you password is incorrect and you named your self abc 123
        # it will show abc 123 with profile image
        invalid_form.context_data['user'] = self.request.user
        return invalid_form

    def get_object(self, queryset=None):

        return self.request.user


class LikeApiView(APIView):
    def post(self, request,page_id, post_id, *kwargs):
        page_id = self.kwargs['page_id']
        post_id = self.kwargs['post_id']
        comment_urn = self.request.data.get('urn')
        like_response = {"response":"error"}
        if self.request.GET.get('page_name') == "facebook":
            try:
                provider_name = "facebook"
                facebook_post = PostModel.objects.get(post_urn__org__provider = provider_name, id=post_id, post_urn__pk=page_id)
                page_post = facebook_post.post_urn.all().filter(pk = page_id).first()
                access_token = page_post.org.access_token
                urn = page_post.urn

                if comment_urn:
                    response = fb_object_like(comment_urn, access_token)
                    like_response['response'] = response[0]
                else:
                    response = fb_object_like(urn, access_token)
                    page_post.is_liked = True
                    page_post.save()
                    like_response['response'] = response[0]
                    like_response['like_count'] = response[1]
            except Exception as e:
                return JsonResponse(e,safe=False)
        elif self.request.GET.get('page_name') == 'linkedin':
            try:
                provider_name = "linkedin"
                linkedin_post = PostModel.objects.get(post_urn__org__provider=provider_name, id=post_id, post_urn__pk=page_id)
                urn = linkedin_post.post_urn.all().filter(pk=page_id).first()
                post_urn = urn.urn
                user = urn.org.user
                social = SocialAccount.objects.get(user=user.id, provider='linkedin_oauth2')

                access_token = urn.org.access_token

                if comment_urn:
                    like_response['response'] = comment_like_linkedin(comment_urn, social, access_token)
                else:
                    response = post_like_linkedin(post_urn, social, access_token)
                    urn.is_liked = True
                    urn.save()
                    like_response['response'] = response[0]
                    like_response['like_count'] = response[1]
            except Exception as e:
                return JsonResponse(e, safe=False)
        else:
            pass
        return JsonResponse(like_response)

    def delete(self, request, page_id, post_id, *kwargs):
        page_id = self.kwargs['page_id']
        post_id = self.kwargs['post_id']
        comment_urn = self.request.GET.get('urn')
        unlike_response = {"like_response":"error"}
        if self.request.GET.get('page_name') == "facebook":
            try:
                provider_name = "facebook"
                facebook_post = PostModel.objects.get(post_urn__org__provider=provider_name, id=post_id, post_urn__pk=page_id)
                page_post = facebook_post.post_urn.all().filter(pk=page_id).first()
                access_token = page_post.org.access_token
                urn = page_post.urn

                if comment_urn:
                    response = fb_object_unlike(comment_urn, access_token)
                    unlike_response['like_response'] = response[0]
                else:
                    response = fb_object_unlike(urn, access_token)
                    page_post.is_liked = False
                    page_post.save()
                    unlike_response['like_response'] = response[0]
                    unlike_response['like_count'] = response[1]
            except Exception as e:
                return JsonResponse(e)
        elif self.request.GET.get('page_name') == 'linkedin':
            try:
                provider_name = "linkedin"
                linkedin_post = PostModel.objects.get(post_urn__org__provider=provider_name, id=post_id,
                                                      post_urn__pk=page_id)
                social = SocialAccount.objects.get(user=linkedin_post.user.id, provider='linkedin_oauth2')
                urn = linkedin_post.post_urn.all().filter(pk=page_id).first()
                post_urn = urn.urn
                access_token = urn.org.access_token

                if comment_urn:
                    unlike_response['like_response'] = delete_comment_like_linkedin(comment_urn, social, access_token)
                else:
                    response = delete_post_like_linkedin(post_urn, social, access_token)
                    urn.is_liked = False
                    urn.save()
                    unlike_response['like_response'] = response[0]
                    unlike_response['like_count'] = response[1]
            except Exception as e:
                return JsonResponse(e)
        else:
            pass
        return JsonResponse(unlike_response)

@csrf_protect
def check_username_exists(request):
    if request.method == 'POST':
        data = json.loads(request.body)  # Parse JSON data
        username = data.get('username', '')



        # Check if the username already exists in the database
        try:
            username = username.strip()
            user = User.objects.get(username=username)
            exists = True
        except User.DoesNotExist:
            exists = False

        data = {
            'exists': exists
        }

        return JsonResponse(data)

    return JsonResponse({'error': 'Invalid request method'}, status=400)
@csrf_protect
def check_email_exists(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        email = data.get('email', '')

        try:
            user = User.objects.get(email=email)
            exists = True
        except User.DoesNotExist:
            exists = False

        data = {
            'exists': exists
        }

        return JsonResponse(data)

    return JsonResponse({'error': 'Invalid request method'}, status=400)
@csrf_protect
def check_company_exists(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        company_name = data.get('company', '')  # Use company_name instead of company

        # Check if the company already exists in the database
        try:
            company = Company.objects.get(name=company_name)
            exists = True
        except Company.DoesNotExist:
            exists = False

        response_data = {
            'exists': exists
        }

        return JsonResponse(response_data)

    return JsonResponse({'error': 'Invalid request method'}, status=400)


@csrf_protect
def passwor_validation(request):
    if request.method == "POST":
        data = json.loads(request.body)
        password_1 = data.get('password','')
        try:
            validate_password(password_1)
        except ValidationError as e:
            error_messages = e.messages
            return JsonResponse({'errors': error_messages})
        else:
            return JsonResponse({'message': True})
    return JsonResponse({'error': 'Invalid request method'}, status=400)