from django.contrib.auth.forms import UserCreationForm,UserChangeForm,PasswordChangeForm
from django import forms
from .models import *
from django.core.exceptions import ValidationError
from django.contrib.auth import login, password_validation, update_session_auth_hash
from allauth.account.forms import LoginForm


class CustomUserCreationForm(UserCreationForm):
    company_name = forms.CharField(max_length=255, required=False,
                                   widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ("email",)
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'company': forms.SelectMultiple(attrs={'class': 'form-control'}),
        }



class CustomUserInvitationForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.fields['company'].required = False  # Make the company field not required

    company = forms.ModelMultipleChoiceField(
        queryset=Company.objects.all(),
        widget=forms.CheckboxSelectMultiple,  # Use checkboxes for multiple selection
        required=False  # Make the field not required
    )
    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ("email", "company")
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),

        }


class CustomUserUpdateForm(UserChangeForm):

    # old_password = forms.CharField(
    #     widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    #     required=False
    # )
    # new_password1 = forms.CharField(
    #     widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    #     required=False
    # )
    # new_password2 = forms.CharField(
    #     widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    #     required=False
    # )
    class Meta(UserChangeForm.Meta):
        model = User
        fields = ['username','first_name','last_name','profile_image','email','bio']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'bio': forms.TextInput(attrs={'class': 'form-control'}),



        }

    def __init__(self, user,request, *args, **kwargs):
        self.user = user
        self.request = request
        super().__init__(*args, **kwargs)



    def clean_old_password(self):

        old_password = self.cleaned_data["old_password"]

        if old_password:
            if not self.user.check_password(old_password):
                raise forms.ValidationError(
                    "Your old password was entered incorrectly. Please enter it again.",
                )
            return old_password

    def clean_new_password2(self):
        password1 = self.cleaned_data.get("new_password1")
        password2 = self.cleaned_data.get("new_password2")
        if (password1 and not password2) or (password2 and not password1) or (password1 and password2 and password1 != password2):
            raise forms.ValidationError("Passwords do not match.")

        elif not password1 and not password2:
            self.cleaned_data['new_password1'] = None
            return
        else:

            try:
                password_validation.validate_password(password2, self.instance)
            except ValidationError as error:
                self.add_error("new_password2", error)
                return
            return password2




    # def save(self, commit=True):
    #     user = super().save(commit=False)
    #     password = self.cleaned_data["new_password2"]
    #     if password:
    #         user.set_password(password)
    #         update_session_auth_hash(self.request, user)
    #         login(self.request,user)
    #     if commit:
    #         # if self.request.POST.get('remove_image'):
    #         #     user.profile_image.delete()
    #         #     user.profile_image = None
    #         user.save()
    #     return user




class PointFileModelForm(forms.ModelForm):
    point_file = forms.FileField(label='Select an point file',
                                 widget=forms.FileInput(attrs={'class': 'custom-file-input'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['point_file'].widget.attrs.update({'class': 'custom-file-input'})

    def clean_audio_file(self):
        point_file = self.cleaned_data.get('point_file')
        if point_file:
            content_type = point_file.content_type
            allowed_content_types = [
                # 'audio/mpeg',
                'txt',
                # Add more accepted audio file types as needed
            ]
            if content_type not in allowed_content_types:
                raise ValidationError('Please upload an txt.')
        return point_file

    class Meta:
        model = PointFileModel
        fields = ('name', 'point_file')

class SharePageForm(forms.ModelForm):
    class Meta:
        model = SharePage
        fields = ('user', 'org_id')


class PostModelForm(forms.ModelForm):
    facebook = forms.BooleanField(widget=forms.CheckboxInput(), required=False)
    instagram = forms.BooleanField(widget=forms.CheckboxInput(), required=False)
    linkedin = forms.BooleanField(widget=forms.CheckboxInput(), required=False)

    class Meta:
        model = PostModel
        fields = ('post', 'facebook', 'instagram', 'linkedin', 'comment_check')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['post'].widget.attrs.update(
            {
                'class': 'description bg-gray-100 sec p-3 h-60 border border-gray-300 outline-none w-full',
                'placeholder': 'Describe Everything about this post'
             })


class CommentForm(forms.Form):
    comment = forms.CharField(widget=forms.Textarea(attrs={'name': 'comment'}))


# class SchedulePostForm(forms.ModelForm):
#     scheduled_date = forms.DateTimeField()
#
#     class Meta:
#         model = ScheduledPost
#         fields = ['scheduled_date']