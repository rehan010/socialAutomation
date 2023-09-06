from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.utils import user_username
from allauth.exceptions import ImmediateHttpResponse
from django.contrib.auth import views as auth_views
from django.contrib.auth import login,update_session_auth_hash
from django.http import response
from .signals import *
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import TemplateView, FormView,CreateView,DeleteView,UpdateView
from .forms import *
import requests
from .restapis import *
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from rest_framework.generics import ListAPIView,DestroyAPIView, RetrieveUpdateAPIView
from rest_framework.views import APIView
from django.db.models import Q
from .serializer import *
from django.views.decorators.csrf import csrf_exempt
from django.utils.safestring import mark_safe
# from django.contrib.auth.models import User
from .models import User
from allauth.socialaccount.models import EmailAddress,SocialAccount,SocialToken
from django.shortcuts import get_object_or_404
from rest_framework import filters

from google.oauth2 import id_token
from google.auth.transport import requests as auth_requests
from django.contrib.auth.mixins import LoginRequiredMixin

from django.shortcuts import render
from allauth.socialaccount.models import SocialToken
from django.utils.timezone import make_aware
from datetime import datetime, date, timedelta
# from .signals import post_update_signal
from django.contrib import messages
from django.contrib.auth import logout
from allauth.socialaccount.views import ConnectionsView
from django.utils.html import escape



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

class ProfileView(LoginRequiredMixin,TemplateView):
    template_name = "registration/profile.html"
class UserView(LoginRequiredMixin,TemplateView):
    template_name = "registration/users.html"
    model = User
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # context['users'] = User.objects.filter(manager=self.request.user)
        # context['invites'] = InviteEmploye.objects.all()
        user_manager = self.request.user.manager
        if user_manager != None:
            context['invites_admin'] = InviteEmploye.objects.filter(Q(invited_by=self.request.user) | Q(invited_by=user_manager))
        context['invites'] = InviteEmploye.objects.filter(invited_by=self.request.user)

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
                user_queryset = queryset.filter(Q(email__icontains=search_query) | Q(username__icontains=search_query), ~Q(manager=self.request.user), ~Q(id=self.request.user.id), Q(is_invited=False))
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
            permission = data.get('permission')

            invite = InviteEmploye.objects.get(pk=invite_id)
            selected_user = User.objects.get(pk=invite.selected_user.id)
            invite.role = role
            invite.permission = permission
            invite.save()
            return JsonResponse({'message': 'New role of' + ' ' + selected_user.username + ' ' + 'is' + ' ' + role + ' with permission' + ' ' + permission})
        else:
            return JsonResponse({'error': 'Selected user not found.'}, status=400)


class assign_manager(CreateView):
    model = InviteEmploye

    def post(self, request, *kwargs):
        if self.request.method == 'POST':
            data = json.loads(request.body)
            user_id = data.get('user')
            email = data.get('email')
            role = data.get('role')
            permission = data.get('permission')
            if role != 'MANAGER':
                permission = "WRITE"

            try:
                token = generate_random_token()

                if email is None:
                    selected_user = User.objects.get(pk=user_id)
                    invite = InviteEmploye(token=token, invited_by=self.request.user, status='PENDING', email=selected_user.email, selected_user=selected_user, role=role, permission=permission)
                    invite.save()
                    selected_user.is_invited = True
                    selected_user.save()
                    reject_link = f"https://localhost:8000/reject_invitation?token={token}"
                    invite_link = f"https://localhost:8000/accept_invitation?token={token}"
                    email = selected_user.email
                    # email = 'anasurrehman5@gmail.com'

                    # Render the email template with the dynamic content
                    context = {'recipient_name': selected_user.username, 'invite_link': invite_link,
                               'reject_link': reject_link}
                    email_subject = 'Invitation to Join Our App'
                    email_body = render_to_string('registration/emails.html', context)

                    # Send the email using Django's email functionality
                    send_mail(email_subject, email_body, 'social_presence@gmail.com', [email])
                else:
                    invite = InviteEmploye(token=token, invited_by=self.request.user, status='PENDING', email=email, role=role, permission=permission)
                    invite.save()


                    invite_link = f"https://localhost:8000/accounts/register/invite?token={token}"
                    # email = selected_user.email
                    email = email

                    # Render the email template with the dynamic content
                    context = {'recipient_name': 'User', 'invite_link': invite_link}
                    email_subject = 'Invitation to Join Our App'
                    email_body = render_to_string('registration/emails.html', context)

                    # Send the email using Django's email functionality
                    send_mail(email_subject, email_body, 'social_presence@gmail.com', [email])

                return JsonResponse({'message': email})

            except User.DoesNotExist:
                return JsonResponse({'error': 'Selected user not found.'}, status=400)

        else:
            return JsonResponse({'error': 'Invalid request method.'}, status=405)


def accept_invitation_view(request):
    token = request.GET['token']
    invite = InviteEmploye.objects.get(token=token)
    user = User.objects.get(pk=invite.selected_user.id)
    if invite:
        user.manager = request.user
        user.company = request.user.company
        user.save()
        invite.status = 'ACCEPTED'
        invite.save()
    login(request, user)

    return render(request, 'registration/invitation_complete.html')


def reject_invitation_view(request):
    token = request.GET['token']
    invite = InviteEmploye.objects.get(token=token)
    user = User.objects.get(pk=invite.selected_user.id)
    if invite:
        invite.status = 'REJECTED'
        invite.save()
        user.is_invited = False
        user.save()

    return render(request, 'registration/register.html')

class UserCreateView(LoginRequiredMixin,TemplateView):
    template_name = "registration/register.html"


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "registration/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = date.today()
        year = timezone.now().year
        curr_date = datetime.now()
        before_date = datetime.now() + timedelta(days=-7)
        week_before_date = before_date + timedelta(days=-7)
        start_of_day = curr_date.replace(hour=0, minute=0, second=0, microsecond=0)
        start = int(start_of_day.timestamp() * 1000)

        # Add your context data here
        if self.request.user.is_authenticated:
            user_manager = self.request.user.manager

            if user_manager != None:
                role = InviteEmploye.objects.get(selected_user=self.request.user, invited_by=self.request.user.manager)
                user_role = role.role
                user_permission = role.permission
                if user_permission == 'HIDE':

                    total_posts = PostModel.objects.filter(user=self.request.user, status='PUBLISHED')
                    sharepages = SharePage.objects.filter(user=self.request.user)

                else:
                    total_posts = PostModel.objects.filter(Q(user=self.request.user) | Q(user=self.request.user.manager), status='PUBLISHED')
                    sharepages = SharePage.objects.filter(Q(user=self.request.user) | Q(user=self.request.user.manager))

                    # org = SharePage.objects.filter(user=self.request.user)

            else:
                invited = InviteEmploye.objects.filter(invited_by=self.request.user, status="ACCEPTED")
                invites = []
                for user in invited:
                    invited_users_id = user.selected_user.id
                    invites.append(invited_users_id)
                total_posts = PostModel.objects.filter(Q(user=self.request.user.id) | Q(user__in=invites), status='PUBLISHED')

                sharepages = SharePage.objects.filter(Q(user=self.request.user) | Q(user__in=invites))

                # org = SharePage.objects.filter(Q(user=self.request.user.id) | Q(user__in=invites))

            results_ln = []
            results_fb = []
            results_insta = []


            current_date = timezone.now().date()

            # Calculate the start date (seven days ago)
            start_date = current_date - timedelta(days=6)


            # Loop through the days of the week
            for day in range(7):
                # Calculate the end date for the current day
                end_date = start_date + timedelta(days=1)

                # Query the database to count the number of posts created on the current day
                post_count_ln = total_posts.filter(post_urn__org__provider='linkedin', created_at__gte=start_date, created_at__lt=end_date).count()
                post_count_fb = total_posts.filter(post_urn__org__provider='facebook', created_at__gte=start_date, created_at__lt=end_date).count()
                post_count_insta = total_posts.filter(post_urn__org__provider='instagram', created_at__gte=start_date, created_at__lt=end_date).count()

                # Append the result to the list
                results_ln.append((start_date.strftime("%A"), post_count_ln))
                results_fb.append((start_date.strftime("%A"), post_count_fb))
                results_insta.append((start_date.strftime("%A"), post_count_insta))

                # Move to the next day
                start_date = end_date

            #Monthly Post Platfrom Wise
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)

            # Initialize lists to store the months and counts for each provider
            months = []  # To store months
            linkedin_counts = []  # To store LinkedIn counts
            facebook_counts = []  # To store Facebook counts
            instagram_counts = []  # To store Instagram counts

            # Loop through each month within the past 30 days
            current_month = start_date.replace(day=1)  # Start with the first day of the start month
            while current_month <= end_date:
                # Calculate the start and end of the current month
                next_month = current_month.replace(day=28) + timedelta(days=4)  # Get the last day of the month
                end_month = next_month - timedelta(days=next_month.day)

                # Query the database to count posts for LinkedIn, Facebook, and Instagram in the current month
                post_count_ln = total_posts.filter(post_urn__org__provider='linkedin', created_at__gte=current_month,
                                                   created_at__lte=end_month).count()
                post_count_fb = total_posts.filter(post_urn__org__provider='facebook', created_at__gte=current_month,
                                                   created_at__lte=end_month).count()
                post_count_insta = total_posts.filter(post_urn__org__provider='instagram',
                                                      created_at__gte=current_month, created_at__lte=end_month).count()

                # Store the current month in the "months" list (assuming all months are the same)
                months.append(current_month.strftime("%B %Y"))

                # Store the counts in their respective provider-specific lists
                linkedin_counts.append(post_count_ln)
                facebook_counts.append(post_count_fb)
                instagram_counts.append(post_count_insta)

                # Move to the next month
                current_month = next_month

            # months = list(monthly_counts_ln.keys())
            # linkedin_counts = list(monthly_counts_ln.values())
            # facebook_counts = list(monthly_counts_fb.values())
            # instagram_counts = list(monthly_counts_insta.values())

            context["linkedin_counts"] = linkedin_counts
            context["facebook_counts"] = facebook_counts
            context["instagram_counts"] = instagram_counts
            context["months"] = months

            labels = []
            values_ln = []
            values_fb = []
            values_insta = []

            for item in results_ln:
                labels.append(item[0])
                values_ln.append(item[1])
            for item in results_fb:
                values_fb.append(item[1])
            for item in results_insta:
                values_insta.append(item[1])

            day_name_mapping = {
                'Monday': 'Mon',
                'Tuesday': 'Tue',
                'Wednesday': 'Wed',
                'Thursday': 'Thu',
                'Friday': 'Fri',
                'Saturday': 'Sat',
                'Sunday': 'Sun'
            }
            label = [day_name_mapping[day] for day in labels]

            context['data_ln'] = values_ln
            context['labels'] = label
            context['data_fb'] = values_fb
            context['data_insta'] = values_insta

            # Post,likes,comments for today
            user_post = total_posts.filter(created_at__date=today)
            likes_today = 0
            comments_today = 0
            likes_overall = 0
            comments_overall = 0
            followers_today = 0
            followers_overall = 0

            linkedin_org = sharepages.filter(provider="linkedin")
            if len(linkedin_org) > 0:
                for page in linkedin_org:

                    org_id = page.org_id
                    access_token = page.access_token


                    result = linkedin_share_stats(org_id, access_token, start)
                    likes = result[0]
                    comments = result[1]

                    likes_today += likes
                    comments_today += comments

                    result = linkedin_share_stats_overall(org_id, access_token)
                    likes_ovr = result[0]
                    comments_ovr = result[1]

                    likes_overall += likes_ovr
                    comments_overall += comments_ovr

                    result = linkedin_followers_today(org_id, access_token, start)
                    followers = result
                    followers_today += followers
                    result = linkedin_followers(org_id, access_token)
                    followers_ovr = result
                    followers_overall += followers_ovr

            fb_org = sharepages.filter(provider="facebook")
            if len(fb_org) > 0:
                for page in fb_org:
                    page_id = page.org_id
                    access_token = page.access_token

                    result = fb_page_insights(access_token, page_id)
                    likes = result[0]
                    comments = result[1]
                    newfollowers_today = result[2]

                    followers_today += newfollowers_today
                    likes_today += likes
                    comments_today += comments


                    # result = linkedin_followers_today(org_id, access_token, start)
                    # followers = result
                    # followers_today += followers
                    # result = linkedin_followers(org_id, access_token)
                    # followers_ovr = result
                    # followers_overall += followers_ovr

            insta_accounts = sharepages.filter(provider="instagram")
            if len(insta_accounts) > 0:
                for account in insta_accounts:
                    access_token = account.access_token
                    account_id = account.org_id

                    result = instagram_page_insigths(access_token, account_id)
                    likes = result[0]
                    comments = result[1]

                    likes_today += likes
                    comments_today += comments




                    #
                    # result = linkedin_followers_today(org_id, access_token, start)
                    # followers = result
                    # followers_today += followers
                    # result = linkedin_followers(org_id, access_token)
                    # followers_ovr = result
                    # followers_overall += followers_ovr


            #Weekly comparison
            current_week_post = len(total_posts.filter(created_at__lte=curr_date, created_at__gte=before_date))
            previous_week_post = len(total_posts.filter(created_at__lte=before_date, created_at__gte=week_before_date))
            if previous_week_post > 0:
                change_per = round((current_week_post - previous_week_post)*(100/previous_week_post), 1)
            else:
                change_per = 100

            context['likes_today'] = likes_today
            context['post_percentage'] = change_per
            context['likes'] = likes_overall
            context['comments_today'] = comments_today
            context['comments'] = comments_overall
            context['total_posts'] = len(total_posts)
            context['post_today'] = len(user_post)
            context['followers_today'] = followers_today
            context['followers_overall'] = followers_overall


        return context


class PasswordResetView(auth_views.PasswordResetView):
    template_name = "registration/my_password_reset_form.html"


class PasswordResetDoneView(auth_views.PasswordResetDoneView):
    template_name = "registration/my_password_reset_done.html"
    success_url = reverse_lazy("password_change_done")


class ConnectPageView(LoginRequiredMixin, CreateView):
    model = SharePage
    form_class = SharePageForm
    template_name = 'social/connection.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add your context data here
        # if self.request.user.is_authenticated:
        #     point_files = list(PointFileModel.objects.filter(user=self.request.user,is_deleted=False).values('id','name','point_file'))
        #     lat_long= {}
        #     for _ in point_files:
        #         lat_long_list = list(LatLongModel.objects.filter(file=_['id']).values('latitude', 'longitude'))
        #         # Convert Decimal values to float
        #         _['lat_long'] = [{'latitude': float(lat['latitude']), 'longitude': float(lat['longitude'])} for lat
        #                             in lat_long_list]

        user = self.request.user  # Set the user to the logged-in user
        social = SocialAccount.objects.filter(user=user.id)
        access_token = {}
        for _ in social:
            access_token[_.provider] = SocialToken.objects.filter(account_id=_)





        my_list = []
        #

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
                # SharePage.objects.create(user=social,organizations_id=id)
                SharePage.objects.create(user=self.request.user,organizations_id=id)

        return redirect(reverse("ln_posts", kwargs={'pk': self.request.user.id}))



class PasswordChangeDoneView(LoginRequiredMixin,auth_views.PasswordChangeDoneView):
    template_name = "registration/my_password_change_done.html"


class PasswordChangeView(LoginRequiredMixin,auth_views.PasswordChangeView):
    template_name = "registration/my_password_change_form.html"


class RegisterView(FormView):
    template_name = "registration/register.html"
    form_class = CustomUserCreationForm

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect(reverse("dashboard"))


class RegisterViewInvite(FormView):
    template_name = "registration/invitation.html"
    form_class = CustomUserInvitationForm

    def get(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            logout(request)
        return super().get(request, *args, **kwargs)


    def form_valid(self, form):


        token = self.request.GET['token']
        email = self.request.POST.get('email')
        email_invite = InviteEmploye.objects.filter(selected_user__email=email)
        email_user = User.objects.filter(email=email)

        if email_invite.exists():
            messages.error(self.request, 'A user with this email already exists.')
            return self.form_invalid(form)
        if email_user.exists():
            messages.error(self.request, 'A user with this email already exists.')
            return self.form_invalid(form)

        invite = InviteEmploye.objects.filter(token=token, email=email)

        if invite:
            invite = InviteEmploye.objects.get(token=token, email=email)
            user = form.save()
            user.manager = invite.invited_by
            user.company = invite.invited_by.company
            user.save()
            invite.selected_user = user
            invite.status = 'ACCEPTED'
            invite.save()
        else:
            messages.error(self.request, 'Invitation was sent to different email address')
            return self.form_invalid(form)


        login(self.request, user)


        return redirect(reverse("dashboard"))

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        token = self.request.GET['token']
        invite = InviteEmploye.objects.get(token=token)
        if invite:
            # Retrieve the 'company' query parameter from the URL and pass it to the form
            kwargs['initial'] = {'company': invite.invited_by.company}
        else:
            kwargs['initial'] = {'company': 'Type in your own company'}

        return kwargs


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
        for _ in social:
            # For Faceboook
            if _.provider == 'facebook':
                data["facebook"] = []
                data["instagram"] = []
                page_data = facebook_page_data(access_token.get(_.user.username).get("facebook"),access_token[_.user.username]['id'])
                data["facebook"] += page_data
                insta_data = get_instagram_user_data(access_token.get(_.user.username).get("facebook"),access_token[_.user.username]['id'])
                data["instagram"] += insta_data
            # For Instagram



            if _.provider == 'linkedin_oauth2':
                data['linkedin'] = []
                linkedin_page = linkedin_get_user_organization(access_token.get(_.user.username).get("linkedin_oauth2"),access_token[_.user.username]['id'])
                data['linkedin'] += linkedin_page

        self.request.session['context'] = data



        return JsonResponse(data)


class PostDraftView(UpdateView):
    model = PostModel
    form_class = PostModelForm
    template_name = 'social/publish_drafts.html'
    success_url = reverse_lazy('my_posts')

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


class PostsGetView(LoginRequiredMixin, TemplateView):
    template_name = 'social/my_posts.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user_manager = self.request.user.manager



        if user_manager != None:
            role = InviteEmploye.objects.get(selected_user=self.request.user, invited_by=self.request.user.manager)
            user_role = role.role
            user_permission = role.permission
            if user_permission == 'HIDE':
                provider_name = "linkedin"
                if len(PostModel.objects.filter(user=self.request.user.pk, prepost_page__provider=provider_name)) > 0:

                    linkedin_post = PostModel.objects.filter(user=self.request.user.pk,
                                                             prepost_page__provider=provider_name).distinct()
                else:
                    linkedin_post = ''

                provider_name1 = "facebook"
                provider_name2 = "instagram"
                if len(PostModel.objects.filter(
                        Q(prepost_page__provider=provider_name1) | Q(prepost_page__provider=provider_name2),
                        user=self.request.user.pk)) > 0:

                    # facebook_post = PostModel.objects.filter(post_urn__org__provider=provider_name1)
                    facebook_post = PostModel.objects.filter(user=self.request.user.pk,
                                                             prepost_page__provider=provider_name1).distinct()
                    instagram_post = PostModel.objects.filter(user=self.request.user.pk,
                                                              prepost_page__provider=provider_name2).distinct()

                else:
                    facebook_post = ''
                    instagram_post = ''

                provider_name3 = "Google Books"

                if len(PostModel.objects.filter(user=self.request.user.pk, prepost_page__provider=provider_name3)) > 0:
                    google_post = PostModel.objects.filter(user=self.request.user.pk,
                                                           prepost_page__provider=provider_name3).distinct()
                else:
                    google_post = ''
            else:
                provider_name = "linkedin"
                posts = PostModel.objects.filter(Q(user=self.request.user.id) | Q(user=self.request.user.manager.id))


                if len(posts.filter(prepost_page__provider=provider_name)) > 0:
                    linkedin_post = posts.filter(prepost_page__provider=provider_name).distinct()
                else:
                    linkedin_post = ''

                provider_name1 = "facebook"
                provider_name2 = "instagram"

                if len(posts.filter(Q(prepost_page__provider=provider_name1)|Q(prepost_page__provider=provider_name2))) > 0:

                    facebook_post = posts.filter(prepost_page__provider=provider_name1).distinct()
                    instagram_post = posts.filter(prepost_page__provider=provider_name2).distinct()

                else:
                    facebook_post = ''
                    instagram_post = ''

                provider_name3 = "Google Books"

                if len(posts.filter(prepost_page__provider=provider_name3)) > 0:
                    google_post = posts.filter(prepost_page__provider=provider_name3).distinct()
                else:
                    google_post = ''
        else:
            invited = InviteEmploye.objects.filter(invited_by=self.request.user,status = "ACCEPTED")
            invites = []
            for user in invited:
                invited_users_id = user.selected_user.id
                invites.append(invited_users_id)
            posts = PostModel.objects.filter(Q(user=self.request.user.id) | Q(user__in=invites))

            provider_name = "linkedin"
            if len(posts.filter(prepost_page__provider=provider_name)) > 0:

                linkedin_post = posts.filter(prepost_page__provider=provider_name).distinct()
            else:
                linkedin_post = ''

            provider_name1 = "facebook"
            provider_name2 = "instagram"
            if len(posts.filter(Q(prepost_page__provider=provider_name1)|Q(prepost_page__provider=provider_name2))) > 0:


            # facebook_post = PostModel.objects.filter(post_urn__org__provider=provider_name1)
                facebook_post = posts.filter(prepost_page__provider=provider_name1).distinct()
                instagram_post = posts.filter(prepost_page__provider=provider_name2).distinct()

            else:
                facebook_post = ''
                instagram_post = ''


            provider_name3 = "Google Books"

            if len(posts.filter(prepost_page__provider=provider_name3)) > 0:
                google_post = posts.filter(prepost_page__provider=provider_name3).distinct()
            else:
                google_post = ''


        context = {
            # 'ids': ids,
            # 'data_list': data_list,
            'posts': PostModel.objects.filter(user_id=self.request.user.id),
            'google_post': google_post,

            'instagram_post': instagram_post,

            'facebook_post': facebook_post,

            'linkedin_post': linkedin_post,

        }

        return context
from django.http import JsonResponse

class PostDeleteView(DestroyAPIView):
    queryset = PostModel.objects.all()
    serializer_class = PostImageSerializer
    def delete(self, request, *args, **kwargs):
        page_id = self.request.GET.get('page_id')

        comment_urn = self.request.data.get('urn')
        response = {}
        response['user'] = self.request.user.id
        post = self.get_object()
        if self.request.GET.get('page_name') == "facebook":
            try:
                post_urn = post.post_urn.all().filter(pk=page_id).first()
                access_token = post_urn.org.access_token
                urn = post_urn.urn

                if comment_urn:
                    response['message'] = delete_meta_posts_comment(access_token,comment_urn)
                    response['request'] = "comment"
                else:
                    response['message'] = delete_meta_posts_comment(access_token,urn)
                    response['request'] = "post"

                    if response['message'] == 'success':
                        post.post_urn.remove(post_urn)
                        if len(post.post_urn.all()) == 0:
                            post.delete()



            except Exception as e:
                return 'falied'

        elif self.request.GET.get('page_name') == "instagram":
            try:


                page_post = post.post_urn.all().filter(pk=page_id).first()
                access_token = page_post.org.access_token
                urn = page_post.urn

                if comment_urn:
                    response['message'] = delete_meta_posts_comment(access_token, comment_urn)
                    response['request'] = 'comment'

            except Exception as e:
                return 'falied'

        elif self.request.GET.get('page_name') == "linkedin":
            try:
                urn = post.post_urn.all().filter(pk=page_id).first()
                post_urn = urn.urn
                user = urn.org.user
                social = SocialAccount.objects.get(user=user.id, provider='linkedin_oauth2')

                access_token = urn.org.access_token

                if comment_urn:
                    pass
                else:
                    pass

            except Exception as e:
                return 'falied'

        return JsonResponse(response)





        # self.destroy(request, *args, **kwargs)
        return JsonResponse({'message': 'Object deleted successfully.'})




class PostsDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'social/post_detail.html'


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
                    else:
                        result = linkedin_post_socialactions(urn, access_token_string, linkedin_post)
                        no_likes = result[0]
                        no_comments = result[1]
                        data = result[2]

            context = {
                'ids': urn,
                'no_likes': no_likes,
                'no_comments': no_comments,
                'data': data,
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
                result = fb_socialactions(urn, access_token_string)
                no_likes = result[0]
                no_comments = result[1]
                data = result[2]

            context = {
                'ids': urn,
                'no_likes': no_likes,
                'is_liked': is_liked,
                'no_comments': no_comments,
                'data': data,
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

                result = insta_socialactions(urn, access_token)
                no_likes = result[0]
                no_comments = result[1]
                data = result[2]


            context = {
                'ids': urn,
                'no_likes': no_likes,
                'no_comments': no_comments,
                'data': data,
                'posts': PostModel.objects.filter(user_id=self.request.user.id),
                'post': instagram_post,
                'posted_on': posted_on,
                'post_id': post_id,
                'page_id': page_id,
                'provider_name': provider_name,
                'reply_media_counter': 0
            }




        # data_list = []
        # for id in ids:
        #     linkedin_org_stats(access_token_string, id, data_list)
        #
        # provider_name1 = "Facebook"
        # facebook_post = PostModel.objects.get(post_urn__org__provider=provider_name1)
        #
        # provider_name2 = "Instagram"
        # instagram_post = PostModel.objects.get(post_urn__org__provider=provider_name2)
        #
        # provider_name3 = "Google Books"
        # google_post = PostModel.objects.get(post_urn__org__provider=provider_name3)

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
        media = request.FILES.get('comment_media')
        post_id = self.kwargs['post_id']
        page_id = self.kwargs['page_id']

        reply_list = request.POST.getlist('reply')
        reply_data = {}
        reply_media_counter = 1
        for comment_urn, reply in zip(comment_urn_list, reply_list):
            reply_data[comment_urn] = [reply]
            reply_media = request.FILES.get(f"reply_media_{reply_media_counter}")
            reply_data[comment_urn].append(reply_media)
            reply_media_counter = reply_media_counter+1


        if comment != ''  or media != None and len(reply_list)==0:
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
                provider_name = "facebook"
                facebook_post = PostModel.objects.get(post_urn__org__provider=provider_name, id=post_id,
                                                      post_urn__pk=page_id)

                post_urn = facebook_post.post_urn.all().filter(pk=page_id).first()

                access_token = post_urn.org.access_token
                for comment_urn, reply in reply_data.items():
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


class ConnectionView(ConnectionsView):

    def get_context_data(self, **kwargs):
        context = super(ConnectionView, self).get_context_data()

        from allauth.socialaccount.models import SocialApp

        social_apps = SocialApp.objects.all()

        for apps in social_apps:
            context[f'{apps.provider}_app'] = apps
            try:
                context[f'{apps.provider}'] = SocialAccount.objects.filter(user=self.request.user.id, provider=apps.provider).first()

            except Exception as e:
                e

        return context

class SocialProfileView(LoginRequiredMixin,TemplateView):
    template_name = 'social/social_profile.html'

    def get_context_data(self, **kwargs):
        provider_name = self.request.GET.get('provider_name')
        providertoGetdetails = self.request.GET.get('provider_name')
        user = self.request.user

        if provider_name == "instagram":
            provider_name = "facebook"

        user_manager = self.request.user.manager

        if user_manager:
            selected_user = InviteEmploye.objects.get(selected_user=self.request.user,
                                                      invited_by=self.request.user.manager)
            role = selected_user.role


            if role == "ADMIN":
                social = SocialAccount.objects.filter(Q(user=user.id) | Q(user=user_manager.id), provider=provider_name)
            else:
                social = SocialAccount.objects.filter(Q(user=user.id), provider=provider_name)

        else:
            social = SocialAccount.objects.filter(Q(user=user.id), provider=provider_name)
        access_token = {}
        data = {}

        for _ in social:
                access_token[_.user.id] = SocialToken.objects.filter(account_id=_).first().token


        user_access_token = access_token[user.id]

        if providertoGetdetails == "facebook":
            try:
                data = fb_page_detail(user_access_token)
                if data.get('error') != None:
                    raise Exception(data['error'])

                data['pages'] = {}
                for _ in social:
                    response = facebook_page_data(access_token.get(_.user.id),_.user.id)
                    data['pages'][_.user.id] = response
                data['provider'] = "facebook"
            except Exception as e:
                data['error'] = e

        elif providertoGetdetails == "instagram":
            try:
                accounts = get_instagram_user_data(user_access_token,user.id)
                instagram__connected_social_account = SocialAccount.objects.get( user = user.id,provider = "instagram")
                data['pages'] = {}
                for account in accounts:
                    if account.get('username') == instagram__connected_social_account.extra_data.get('username'):
                       data.update(instagram_details(user_access_token,account['id']))
                       if data.get("error") != None:
                            raise Exception(data['error'])

                data['pages'][user.id] = accounts

                access_token.pop(user.id)

                for user_id in access_token:
                    accounts = get_instagram_user_data(access_token[user_id],user_id)
                    data['pages'][user_id] = accounts

            except Exception as e:
                data['error'] = e
        elif providertoGetdetails == "instagram":
            try:
                accounts = get_instagram_user_data(user_access_token,user.id)
                instagram__connected_social_account = SocialAccount.objects.get( user = user.id,provider = "instagram")
                data['pages'] = {}
                for account in accounts:
                    if account.get('username') == instagram__connected_social_account.extra_data.get('username'):
                       data.update(instagram_details(user_access_token,account['id']))
                       if data.get("error") != None:
                            raise Exception(data['error'])

                data['pages'][user.id] = accounts

                access_token.pop(user.id)

                for user_id in access_token:
                    accounts = get_instagram_user_data(access_token[user_id],user_id)
                    data['pages'][user_id] = accounts

            except Exception as e:
                data['error'] = e





        context = data
        return context

class EditUserView(LoginRequiredMixin,UpdateView):
    template_name =  'registration/edituser.html'
    model = User
    form_class = CustomUserUpdateForm
    success_url = reverse_lazy('my_profile')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs['request'] = self.request
        return kwargs

    def form_invalid(self, form):
        invalid_form = super(EditUserView,self).form_invalid((form))
        invalid_form.context_data['user'] = self.request.user
        return invalid_form


    def form_valid(self, form):
        # checkbox = self.request.POST.get('remove_image')
        # if(checkbox):
        #     user = form.user
        #     user.profile_image.delete()
        #     user.profile_image = None
    #     form.save()
    #     return super().form_valid(form)
        old_password = form.cleaned_data.get("old_password")
        new_password1 = form.cleaned_data.get("new_password1")
        new_password2 = form.cleaned_data.get("new_password2")

        if old_password and not self.request.user.check_password(old_password):
            form.add_error('old_password',"Your old password was entered incorrectly. Please enter it again.")
            return self.form_invalid(form)

        if new_password1 and new_password2 and new_password1!=new_password2:
            form.add_error("new_password2", "Passwords do not match.")
            return self.form_invalid(form)

        try:
        # Validate new password
            password_validation.validate_password(new_password2, self.request.user)

        except forms.ValidationError as error:
            form.add_error("new_password2", error)
            return self.form_invalid(form)

        return super().form_valid(form)



class LikeApiView(APIView):
    def post(self, request,page_id, post_id, *kwargs):
        page_id = self.kwargs['page_id']
        post_id = self.kwargs['post_id']
        comment_urn = self.request.data.get('urn')
        like_response = "Enter Valid Urn"
        if self.request.GET.get('page_name') == "facebook":
            try:
                provider_name = "facebook"
                facebook_post = PostModel.objects.get(post_urn__org__provider = provider_name, id=post_id, post_urn__pk=page_id)
                page_post = facebook_post.post_urn.all().filter(pk = page_id).first()
                access_token = page_post.org.access_token
                urn = page_post.urn

                if comment_urn:
                    like_response = fb_object_like(comment_urn, access_token)
                else:
                    like_response = fb_object_like(urn, access_token)
                    page_post.is_liked = True
                    page_post.save()
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
                    like_response = comment_like_linkedin(comment_urn, social, access_token)
                else:
                    like_response = post_like_linkedin(post_urn, social, access_token)
                    urn.is_liked = True
                    urn.save()
            except Exception as e:
                return JsonResponse(e, safe=False)
        else:
            pass
        return JsonResponse(like_response)

    def delete(self, request, page_id, post_id, *kwargs):
        page_id = self.kwargs['page_id']
        post_id = self.kwargs['post_id']
        comment_urn = self.request.data.get('urn')
        unlike_response = "Enter Valid Urn"
        if self.request.GET.get('page_name') == "facebook":
            try:
                provider_name = "facebook"
                facebook_post = PostModel.objects.get(post_urn__org__provider=provider_name, id=post_id, post_urn__pk=page_id)
                page_post = facebook_post.post_urn.all().filter(pk=page_id).first()
                access_token = page_post.org.access_token
                urn = page_post.urn

                if comment_urn:
                    unlike_response = fb_object_unlike(comment_urn, access_token)
                else:
                    unlike_response = fb_object_unlike(urn, access_token)
                    page_post.is_liked = False
                    page_post.save()
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
                    unlike_response = delete_comment_like_linkedin(comment_urn, social, access_token)
                else:
                    unlike_response = delete_post_like_linkedin(post_urn, social, access_token)
                    urn.is_liked = False
                    urn.save()
            except Exception as e:
                return JsonResponse(e)
        else:
            pass
        return JsonResponse(unlike_response)





