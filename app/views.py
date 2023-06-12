from django.contrib.auth import views as auth_views
from django.contrib.auth import login
from django.shortcuts import redirect, render
from django.urls import reverse,reverse_lazy
from django.views.generic import TemplateView, FormView,CreateView,DeleteView
from .forms import *
import requests

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
        return context


class PasswordResetView(auth_views.PasswordResetView):
    template_name = "registration/my_password_reset_form.html"


class PasswordResetDoneView(auth_views.PasswordResetDoneView):
    template_name = "registration/my_password_reset_done.html"
    success_url = reverse_lazy("password_change_done")


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

    def form_valid(self, form):
        post = form.save(commit=False)
        post.user = self.request.user  # Set the user to the logged-in user
        post.save()
        access_token = self.request.POST.get('access_token')
        print(access_token)

        access_token = access_token
        message = 'Hello, Facebook!'

        # Create the API endpoint URL
        url = f"https://graph.facebook.com/v17.0/me/feed"
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        data = {
            "message": message
        }
        response = requests.get(url, headers=headers, data=data)
        print(response.json())

        return redirect(reverse("my_posts",kwargs={'pk': self.request.user.id}))


class PostsGetView(TemplateView):
    template_name = 'social/my_posts.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['posts']=PostModel.objects.filter(user_id=self.request.user.id)
        return context



