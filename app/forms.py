from django.contrib.auth.forms import UserCreationForm
from django import forms
from .models import *
from django.core.exceptions import ValidationError


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ("email", "bio", "company")
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'bio': forms.TextInput(attrs={'class': 'form-control'}),
            'company': forms.TextInput(attrs={'class': 'form-control'}),
        }


class CustomUserInvitationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ("email", "bio", "company")
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'bio': forms.TextInput(attrs={'class': 'form-control'}),
            'company': forms.TextInput(attrs={'class': 'form-control'}),
        }



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
    facebook = forms.BooleanField(widget=forms.CheckboxInput(),required=False)
    instagram = forms.BooleanField(widget=forms.CheckboxInput(),required=False)
    linkedin = forms.BooleanField(widget=forms.CheckboxInput(),required=False)

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