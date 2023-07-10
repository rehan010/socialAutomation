from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.utils import user_username
from allauth.exceptions import ImmediateHttpResponse
from django.contrib.auth import views as auth_views
from django.contrib.auth import login
from django.http import response
from django.shortcuts import redirect, render
from django.urls import reverse,reverse_lazy
from django.views.generic import TemplateView, FormView,CreateView,DeleteView
from .forms import *
import requests
from .restapis import *
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth.models import User
from allauth.socialaccount.models import EmailAddress,SocialAccount,SocialToken

from google.oauth2 import id_token
from google.auth.transport import requests as auth_requests

from django.shortcuts import render
from allauth.socialaccount.models import SocialToken
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
        print(f"Token verification failed: {response.text}")
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
        print(f"Token verification failed: {str(e)}")
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

class DashboardView(TemplateView):
    template_name = "registration/base.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add your context data here
        if self.request.user.is_authenticated:
            context['point_files'] = list(PointFileModel.objects.filter(user=self.request.user,is_deleted=False).values('id','name','point_file'))
            lat_long= {}
            for _ in context['point_files']:
                lat_long_list = list(LatLongModel.objects.filter(file=_['id']).values('latitude', 'longitude'))
                # Convert Decimal values to float
                _['lat_long'] = [{'latitude': float(lat['latitude']), 'longitude': float(lat['longitude'])} for lat
                                    in lat_long_list]
            # my_business_view(self.request)

        return context


class PasswordResetView(auth_views.PasswordResetView):
    template_name = "registration/my_password_reset_form.html"


class PasswordResetDoneView(auth_views.PasswordResetDoneView):
    template_name = "registration/my_password_reset_done.html"
    success_url = reverse_lazy("password_change_done")


class ConnectPageView(CreateView):
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
        print(social)
        access_token = {}
        for _ in social:
            access_token[_.provider] = SocialToken.objects.filter(account_id=_)


        print(access_token)



        # access_token_string = ', '.join(str(obj) for obj in access_token)
        # posts = PostModel.objects.filter(user=user.id)


        # names_with_ids = {}
        my_list = []
        #

        data=my_list

        # context
        # 'point_files': point_files

        context = { 'data': data}
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
                SharePage.objects.create(user=social,organizations_id=id)

        return redirect(reverse("ln_posts", kwargs={'pk': self.request.user.id}))



class PasswordChangeDoneView(auth_views.PasswordChangeDoneView):
    template_name = "registration/my_password_change_done.html"


class PasswordChangeView(auth_views.PasswordChangeView):
    template_name = "registration/my_password_change_form.html"


class RegisterView(FormView):
    template_name = "registration/register.html"
    form_class = CustomUserCreationForm

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect(reverse("dashboard"))


class PointFileCreateView(CreateView):
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


class PointFileDeleteView(DeleteView):
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
    model = PostModel
    form_class = PostModelForm
    template_name = 'social/create_post.html'
    success_url = reverse_lazy('my_posts')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user  # Set the user to the logged-in user
        social = SocialAccount.objects.filter(user=user.id)
        access_token = {}
        for _ in social:
            access_token[_.provider] = SocialToken.objects.filter(account_id=_)[0].token

        # Making Data
        data = {}

        # For Faceboook

        page_data = facebook_page_data(access_token.get("facebook"))

        data["facebook_page"] = page_data
        # For Instagram

        insta_data = instagram_id(access_token.get("facebook"))

        data["insta_data"] = insta_data

        self.request.session['context'] = data

        context = {"data":data,'form':self.get_form()}
        return context

    def form_invalid(self, form):
        print(self.request.POST)
        print(self.request.POST.getlist("facebook[]"))
        print( self.request.FILES.get('file'))

        return redirect(reverse("my_posts",kwargs={'pk': self.request.user.id}))
    def form_valid(self, form):
        # print(self.request.session.get('context'))
        requestdata = dict(self.request.POST)

        # Remove csrf token from dict
        requestdata.pop("csrfmiddlewaretoken")

        caption = requestdata.pop("post")
        media = requestdata.pop("media")

        images = media[0].split(",")

        post = form.save(commit=False)
        post.user = self.request.user  # Set the user to the logged-in user
        image = save_image_from_url(media[0])

        post.post = caption[0]
        post.file.save("converted_image.jpg",image)
        # post.save()
        # text = self.request.POST.get("post")





        # Contain only platforms

        context = self.request.session.get('context')
        for platform in requestdata:

            if platform == "facebook":
                socialaccount = SocialAccount.objects.get(user=self.request.user, provider="facebook")
                access_token = SocialToken.objects.filter(account=socialaccount)[0]

                for page in requestdata.get("facebook"):
                    i = 0
                    while context.get('facebook_page')[i].get('id') != page:
                        i += 1

                    # print((context.get('facebook_page')[i].get('id')))
                    info = context.get('facebook_page').pop(i)

                    ispageexist = SharePage.objects.filter(organizations_id=info.get('id')).exists()
                    # Store Shared Page
                    if ispageexist:
                        sharepage = SharePage.objects.get(organizations_id=info.get('id'))
                        sharepage.post.add(post)

                    else:
                        sharepage = SharePage.objects.create(user=socialaccount)
                        # sharepage.user = self.request.user.id
                        sharepage.post.add(post)
                        sharepage.name = info.get('name')
                        sharepage.access_token = info.get('access_token')
                        sharepage.organizations_id = info.get('id')
                        sharepage.provider = "facebook"
                        sharepage.save()

                    # If publishnow exist
                    # print(sharepage)
                    data = {
                        'page_id': sharepage.organizations_id,
                        'page_access_token': sharepage.access_token
                    }
                    if len(images)>1:
                        data = facebookmultiimage(self.request,data,images)
                    else:

                        data = facebookpost(self.request, data)

            elif(platform == "instagram" ):
                    socialaccount = SocialAccount.objects.get(user=self.request.user, provider="facebook")
                    access_token = SocialToken.objects.filter(account=socialaccount)[0]

                    info = context.pop("insta_data")

                    ispageexist = SharePage.objects.filter(organizations_id=info.get('id')).exists()
                    # Store Shared Page
                    if ispageexist:
                        sharepage = SharePage.objects.get(organizations_id=info.get('id'))
                        sharepage.post.add(post)

                    else:
                        sharepage = SharePage.objects.create(user=socialaccount)
                        # sharepage.user = self.request.user.id
                        sharepage.post.add(post)
                        sharepage.name = info.get('name')
                        sharepage.access_token = info.get('access_token')
                        sharepage.organizations_id = info.get('id')
                        sharepage.provider = "instagram"
                        sharepage.save()

                    data = {
                        "insta_id":sharepage.organizations_id
                    }

                    if(len(images)>1):
                        instagrammultiimage(self.request,data,access_token,images)
                    else:
                        instagrampost(self.request,data,access_token)












        return redirect(reverse("my_posts",kwargs={'pk': self.request.user.id}))
        # return None

class PostsGetView(TemplateView):
    template_name = 'social/my_posts.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['posts']=PostModel.objects.filter(user_id=self.request.user.id)
        return context



class InstagramRedirectUri(TemplateView):
    template_name = 'registration/instagram.html'


class FacebookRedirectUri(TemplateView):
    template_name = "registration/facebook.html"


