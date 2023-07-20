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
from django.contrib.auth.mixins import LoginRequiredMixin

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

class BaseView(TemplateView):
    template_name = "registration/base.html"

class ProfileView(LoginRequiredMixin,TemplateView):
    template_name = "registration/profile.html"
class UserView(LoginRequiredMixin,TemplateView):
    template_name = "registration/users.html"

class UserCreateView(LoginRequiredMixin,TemplateView):
    template_name = "registration/user_create.html"


class DashboardView(LoginRequiredMixin,TemplateView):
    template_name = "registration/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add your context data here
        if self.request.user.is_authenticated:
            context['point_files'] = list(PointFileModel.objects.filter(user=self.request.user.pk,is_deleted=False).values('id','name','point_file'))
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


class ConnectPageView(LoginRequiredMixin,CreateView):
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


class PointFileCreateView(LoginRequiredMixin,CreateView):
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
        user = self.request.user  # Set the user to the logged-in user
        social = SocialAccount.objects.filter(user=user.id)
        access_token = {}
        data = {}
        for _ in social:
            access_token[_.provider] = SocialToken.objects.filter(account_id=_)[0].token

        # Making Data

            # For Faceboook
            if _.provider == 'facebook':

                page_data = facebook_page_data(access_token.get("facebook"))

                data["facebook_page"] = page_data
            # For Instagram
            if _.provider == 'instagram':

                insta_data = instagram_id(access_token.get("facebook"))

                data["insta_data"] = insta_data
            # print()
            if _.provider == 'linkedin_oauth2':
                linkedin_page = linkedin_get_user_organization(access_token.get("linkedin_oauth2"))
                data['linkedin_page'] = linkedin_page

        comment_check = True
        self.request.session['context'] = data

        context = {'comment_check': comment_check,"data": data, 'form': self.get_form()}
        return context

    def form_invalid(self, form):
        print(self.request.POST)
        print(self.request.POST.getlist("facebook[]"))
        print( self.request.FILES.get('file'))

        return redirect(reverse("my_posts", kwargs={'pk': self.request.user.id}))

    def form_valid(self, form):
        requestdata = dict(self.request.POST)
        context = self.request.session.get('context')
        requestdata.pop("csrfmiddlewaretoken")
        caption = requestdata.pop("post")
        post = form.save(commit=False)
        post.user = self.request.user
        social = SocialAccount.objects.get(user=self.request.user, provider='linkedin_oauth2')
        post.save()
        comment_check = form.cleaned_data.get('comment_check')
        if comment_check:
            post.comment_check = True
        else:
            post.comment_check = False
        post.save()

        for page in requestdata.get("linkedin"):
            i = 0
            while context.get('linkedin_page')[i].get('key') != page:
                i += 1
            info = context.get('linkedin_page').pop(i)
            if SharePage.objects.filter(org_id=page).exists():
                prepost = SharePage.objects.get(org_id=page)
                post.prepost_page.add(prepost)
                post.save()
            else:
                prepost = SharePage.objects.create(org_id=page, provider='linkedin', user=social, name=info['name'])
                prepost.save()
                post.prepost_page.add(prepost)
                post.save()


        # for page in requestdata.get('facebook'):
        #     prepost = SharePage.objects.filter(org_id=page)
        #     post.prepost_page.add(prepost)
        #     post.save()
        # for page in requestdata.get('instagram'):
        #     prepost = SharePage.objects.filter(org_id=page)
        #     post.prepost_page.add(prepost)
        #     post.save()
        # for page in requestdata.get('googlebooks'):
        #     prepost = SharePage.objects.filter(org_id=page)
        #     post.prepost_page.add(prepost)
        #     post.save()
        action = self.request.POST.get('action', '')  # Get the value of the 'action' input field

        if action == 'publish':
            post.status = 'PUBLISHED'
            post.publish_check = True
            post.save()

        images = self.request.FILES.getlist('images')
        print(images)
        image_object = []
        if images:
            for image in images:
                image_object.append(save_files(image, post))
        post.post = caption[0]

        post.save()
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

                    ispageexist = SharePage.objects.filter(org_id=info.get('id')).exists()
                    # Store Shared Page
                    if ispageexist:
                        sharepage = SharePage.objects.get(org_id=info.get('id'))
                        # sharepage.post.add(post)

                    else:
                        sharepage = SharePage.objects.create(user=socialaccount)
                        sharepage.name = info.get('name')
                        sharepage.access_token = info.get('access_token')
                        sharepage.org_id = info.get('id')
                        sharepage.provider = "facebook"
                        sharepage.save()

                    # If publishnow exist
                    # print(sharepage)
                    data = {
                        'page_id': sharepage.org_id,
                        'page_access_token': sharepage.access_token
                    }
                    if len(image_object) > 1:
                        data = facebookmultiimage(self.request, data, image_object,post,sharepage)
                    else:

                        data = facebookpost(self.request, data,image_object[0],post,sharepage)



            elif (platform == "instagram"):
                socialaccount = SocialAccount.objects.get(user=self.request.user, provider="facebook")
                access_token = SocialToken.objects.filter(account=socialaccount)[0]

                info = context.pop("insta_data")

                ispageexist = SharePage.objects.filter(org_id=info.get('id')).exists()
                # Store Shared Page
                if ispageexist:
                    sharepage = SharePage.objects.get(org_id=info.get('id'))

                else:
                    sharepage = SharePage.objects.create(user=socialaccount)
                    sharepage.name = info.get('name')
                    sharepage.access_token = info.get('access_token')
                    sharepage.organizations_id = info.get('id')
                    sharepage.provider = "instagram"
                    sharepage.save()

                data = {
                    "insta_id": sharepage.organizations_id
                }

                if (len(image_object) > 1):
                    instagrammultiimage(self.request, data, access_token, image_object,post,sharepage)
                else:
                    instagrampost(self.request, data, access_token,image_object[0],post,sharepage)

            elif platform == "linkedin":
                socialaccount = SocialAccount.objects.get(user=self.request.user, provider="linkedin_oauth2")
                access_token = SocialToken.objects.filter(account=socialaccount)[0]
                access_token_string = str(access_token)
                for page in requestdata.get("linkedin"):

                    org_id = page
                    image_m = PostModel.objects.get(id=post.id)
                    org = SharePage.objects.get(org_id=page)
                    create_l_multimedia(images, org_id, access_token_string, clean_file,
                                        get_video_urn, image_m, upload_video, post_video_linkedin,
                                        org, get_img_urn, upload_img, post_single_image_linkedin,
                                        post, post_linkedin)



        return redirect(reverse("my_posts", kwargs={'pk': self.request.user.id}))


class PostsGetView(LoginRequiredMixin,TemplateView):
    template_name = 'social/my_posts.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        result = linkedin_retrieve_access_token(self)
        posts = result[0]
        access_token_string = result[1]
        ids = result[2]

        provider_name = "linkedin"
        linkedin_post = PostModel.objects.filter(user=self.request.user.pk,post_urn__org__provider=provider_name).distinct()

        provider_name1 = "facebook"
        # facebook_post = PostModel.objects.filter(post_urn__org__provider=provider_name1)
        facebook_post = PostModel.objects.filter(user=self.request.user.pk,post_urn__org__provider=provider_name1).distinct()

        provider_name2 = "instagram"
        instagram_post = PostModel.objects.filter(user=self.request.user.pk,post_urn__org__provider=provider_name2).distinct()

        provider_name3 = "Google Books"
        google_post = PostModel.objects.filter(user=self.request.user.pk,post_urn__org__provider=provider_name3).distinct()

        #     for post in pages:
        #         org_id = post.org.id
        #         post_urn = post.urn
        #
        #         urn = post_urn
        #         if urn == '' or urn == None:
        #             pass
        #         else:
        #             prefix, value = post_urn.rsplit(':', 1)
        #             if prefix == 'urn:li:ugcPost':
        #                 response = ugcpost_socialactions(urn, access_token_string)
        #             else:
        #                 response = linkedin_post_socialactions(urn, access_token_string)
        #
        #
        # # scheduler = BackgroundScheduler()
        # # scheduler.add_job(schedule_api.create_post, 'interval', minutes=1)  # Adjust the interval as needed
        # # scheduler.start()
        #
        # data_list = []
        # for id in ids:
        #     linkedin_org_stats(access_token_string, id, data_list)
        #

        context = {
            # 'ids': ids,
            # 'data_list': data_list,
            'posts': PostModel.objects.filter(user_id=self.request.user.id),
            'google_post': google_post,
            'instagram_post': instagram_post,
            'facebook_post': facebook_post,
            'linkedin_post': linkedin_post
        }

        return context


class PostsDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'social/post_detail.html'


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        result = linkedin_retrieve_access_token(self)
        posts = result[0]
        access_token_string = result[1]
        ids = result[2]
        social = result[3]
        post_id = self.kwargs['post_id']
        page_id = self.kwargs['page_id']
        posted_on = Post_urn.objects.get(id=page_id).org.name
        name = self.request.GET.get('page_name')


        if self.request.GET.get('page_name') == 'linkedin':

            provider_name = "linkedin"
            linkedin_post = PostModel.objects.get(post_urn__org__provider=provider_name, id=post_id, post_urn__pk=page_id)

            org_id = linkedin_post.post_urn.all().filter(pk=page_id).first().org.org_id
            post_urn = linkedin_post.post_urn.all().filter(pk=page_id).first().urn

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
                'ids': ids,
                'no_likes': no_likes,
                'no_comments': no_comments,
                'data': data,
                'posts': PostModel.objects.filter(user_id=self.request.user.id),
                'post': linkedin_post,
                'posted_on': posted_on,
                'post_id': post_id,
                'provider_name': provider_name
            }

        elif self.request.GET.get('page_name') == 'facebook':
            provider_name = "facebook"

            facebook_post = PostModel.objects.get(post_urn__org__provider=provider_name, id=post_id,post_urn__pk=page_id)
            org_id = facebook_post.post_urn.all().filter(pk=page_id).first().org.org_id
            post_urn = facebook_post.post_urn.all().filter(pk = page_id).first().urn
            access_token_string = facebook_post.post_urn.all().filter(pk=page_id).first().org.access_token
            urn = post_urn
            if urn == '' or urn == None:
                pass
            else:


                result = fb_socialactions(urn,access_token_string)
                no_likes = result[0]
                no_comments = result[1]
                data = result[2]

            context = {
                'ids': urn,
                'no_likes': no_likes,
                'no_comments': no_comments,
                'data': data,
                'posts': PostModel.objects.filter(user_id=self.request.user.id),
                'post': facebook_post,
                'posted_on': posted_on,
                'post_id': post_id,
                'page_id':page_id,
                'provider_name': provider_name
            }
        elif self.request.GET.get('page_name') == 'instagram':
            provider_name = "instagram"
            instagram_post = PostModel.objects.get(post_urn__org__provider=provider_name, id=post_id,post_urn__pk=page_id)
            org_id = instagram_post.post_urn.all().filter(pk=page_id).first().org.org_id
            post_urn = instagram_post.post_urn.all().filter(pk=page_id).first().urn
            facebook_account = SocialAccount.objects.get(user_id = self.request.user.id,provider = "facebook")
            access_token_string = SocialToken.objects.get(account = facebook_account).token
            urn = post_urn
            if urn == '' or urn == None:
                pass
            else:

                result = insta_socialactions(urn, access_token_string)
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
                'provider_name': provider_name
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
    def post(self, request, **kwargs):
        comment = self.request.POST.get('comment')
        comment_urn_list = request.POST.getlist('comment_urn')
        reply_list = request.POST.getlist('reply')
        reply_data = {}
        for comment_urn, reply in zip(comment_urn_list, reply_list):
            reply_data[comment_urn] = reply

        post_id = self.kwargs['post_id']
        page_id = self.kwargs['page_id']
        if comment != '':
            if self.request.GET.get('page_name') == 'linkedin':


                provider_name = "linkedin"
                linkedin_post = PostModel.objects.get(post_urn__org__provider=provider_name, id=post_id,post_urn__pk=page_id)

                org_id = linkedin_post.post_urn.all().filter(pk=page_id).first().org.org_id
                post_urn = linkedin_post.post_urn.all().filter(pk=page_id).first().urn
                result = linkedin_retrieve_access_token(self)

                access_token = result[1]
                social = result[3]
                create_comment(access_token, post_urn, comment, social)

                if len(reply_list) > 0:
                    if self.request.GET.get('page_name') == 'linkedin':
                        provider_name = "linkedin"
                        linkedin_post = PostModel.objects.get(post_urn__org__provider=provider_name, id=post_id,post_urn__pk=page_id)

                        post_urn = linkedin_post.post_urn.all().filter(pk=page_id).first().urn
                        result = linkedin_retrieve_access_token(self)

                        access_token = result[1]
                        social = result[3]
                        for comment_urn, reply in reply_data.items():
                            if reply != '':
                                result = post_nested_comment_linkedin(social, access_token, post_urn, reply, comment_urn)
                            else:
                                pass

                return redirect(reverse("my_detail_posts", kwargs={'post_id': post_id, 'page_id': page_id}) + '?page_name=linkedin')

        elif len(reply_list) > 0:
            if self.request.GET.get('page_name') == 'linkedin':
                provider_name = "linkedin"
                linkedin_post = PostModel.objects.get(post_urn__org__provider=provider_name, id=post_id,post_urn__pk=page_id)

                post_urn = linkedin_post.post_urn.all().filter(pk=page_id).first().urn
                result = linkedin_retrieve_access_token(self)

                access_token = result[1]
                social = result[3]
                for comment_urn, reply in reply_data.items():
                    if reply != '':
                        result = post_nested_comment_linkedin(social, access_token, post_urn, reply, comment_urn)
                    else:
                        pass
            return redirect(reverse("my_detail_posts", kwargs={'post_id': post_id, 'page_id': page_id}) + '?page_name=linkedin')
        else:
            pass

        return redirect(reverse("my_detail_posts", kwargs={'post_id': post_id, 'page_id': page_id}))


class CommentPostView(FormView):
    form_class = CommentForm

    def form_invalid(self, form):
        form
        self.request.POST
        post_id = self.request.POST.get('post_id')  # Assuming post_id is submitted via POST data
        page_id = self.request.POST.get('page_id')  # Assuming page_id is submitted via POST data
        return redirect(reverse('my_detail_posts', kwargs={'post_id': post_id, 'page_id': page_id}))



    def form_valid(self, form):

        urn = self.request.POST.get('id')
        text = self.request.POST.get('comment')
        provider = self.request.POST.get('provider_name')
        post_id = self.request.POST.get('post_id')  # Assuming post_id is submitted via POST data
        page_id = self.request.POST.get('page_id')  # Assuming page_id is submitted via POST data
        # media = self.request.FILES.get("media")  # if media is a file
        media = self.request.POST.get('media')
        access_token = Post_urn.objects.get(urn = urn).org.access_token

        if provider == "facebook":
            commentresponse = fb_post_comments(urn,text,media,access_token)

        elif provider == "instagram":
            facebook_account = SocialAccount.objects.get(user_id=self.request.user.id, provider="facebook")
            access_token_string = SocialToken.objects.get(account=facebook_account).token
            commentresponse = fb_post_comments(urn,text,media,access_token_string)



        redirect_url = reverse('my_detail_posts', kwargs={'post_id': post_id, 'page_id': page_id})
        redirect_url += f'?page_name={provider}'
        return redirect(redirect_url)




class InstagramRedirectUri(TemplateView):
    template_name = 'registration/instagram.html'


class FacebookRedirectUri(TemplateView):
    template_name = "registration/facebook.html"


