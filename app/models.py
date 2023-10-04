# from allauth.socialaccount.models import SocialAccount
# from django.contrib.auth import get_user_model
from django.db import models

from django.utils import timezone
from django.db.models import functions
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager


class CustomUserManager(BaseUserManager):
    use_in_migrations = True
    """
    Custom user model manager where email is the unique identifiers
    for authentication instead of usernames.
    """

    def create_user(self, email, password, **extra_fields):
        """
        Create and save a User with the given email and password.
        """
        extra_fields.setdefault('is_active', False)

        if not email:
            raise ValueError(('The Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)


# Create your models here.
class User(AbstractUser):
    # Add your custom fields here
    # Example:
    age = models.IntegerField(blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    company = models.ManyToManyField('Company')
    manager = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    is_invited = models.BooleanField(default=False)
    profile_image = models.ImageField(upload_to='media', blank=True)
    is_deleted = models.BooleanField(null=False, default=False)



    class Meta:
        constraints = [
            models.UniqueConstraint(
                name='unique_company_case_insensitive',
                fields=[functions.Lower('company')],
            )
        ]
    objects = CustomUserManager()

    class Meta:
        db_table = 'user'
        verbose_name = 'Smart User'
        verbose_name_plural = 'Smart Users'


class BaseModel(models.Model):
    """
    Base model which extends in all models to inherit common fields.
    """
    is_deleted = models.BooleanField(null=False, default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def delete(self):
        self.is_deleted = True
        self.save()

    def restore(self):
        self.is_deleted = False
        self.save()


class InviteEmploye(BaseModel):
    STATUS_CHOICES = [('PENDING', 'PENDING'), ('ACCEPTED', 'ACCEPTED'), ('REJECTED', 'REJECTED')]
    ROLE_CHOICES = [('ADMIN', 'ADMIN'), ('MEMBER', 'MEMBER')]
    PERMISSIONS = [('HIDE', 'HIDE'), ('READ', 'READ'), ('WRITE', 'WRITE')]
    token = models.CharField(max_length=255, blank=True)
    invited_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    email = models.EmailField(("email address"), blank=True)
    status = models.CharField(choices=STATUS_CHOICES, default='PENDING', blank=True)
    selected_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True,
                                      related_name="selected_user")
    role = models.CharField(choices=ROLE_CHOICES, default='MEMBER')
    permission = models.CharField(choices=PERMISSIONS, default='HIDE')
    manager_corp = models.BooleanField(default=False)
    expiration_date = models.DateTimeField(null=True, blank=True)
    is_expired = models.BooleanField(default=False)



    class Meta:
        db_table = 'invite'
        verbose_name = 'Invite Employe'
        verbose_name_plural = 'Invite Employes'

    def __str__(self):
        return self.email + '--' + self.status


class PointFileModel(BaseModel):
    name = models.CharField(max_length=255, blank=True)
    point_file = models.FileField(upload_to='point_file')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)


class LatLongModel(BaseModel):
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    file = models.ForeignKey(PointFileModel, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"Latitude: {self.latitude}, Longitude: {self.longitude}"

class Company(models.Model):
    name = models.TextField(blank=True, null=True, unique=True)

    def __str__(self):
        return self.name


class ImageModel(models.Model):
    image = models.FileField(upload_to='videos/')
    image_urn = models.CharField(max_length=255, blank=True)
    image_posted = models.CharField(max_length=500, blank=True, null=True)
    image_url = models.CharField(max_length=1000, blank=True, null=True)

    def is_mp4_file(self):
        file_extension = self.image.name.split('.')[-1].lower()
        return file_extension == 'mp4'


class PostModel(BaseModel):
    POST_TYPE = [('DRAFT', 'DRAFT'), ('PUBLISHED', 'PUBLISHED'), ('SCHEDULED', 'SCHEDULED'),
                 ('PROCESSING', 'PROCESSING'), ('FAILED', 'FAILED')]
    post = models.TextField(blank=True)
    images = models.ManyToManyField('ImageModel')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    post_urn = models.ManyToManyField('Post_urn')
    prepost_page = models.ManyToManyField('SharePage')
    schedule_datetime = models.DateTimeField(blank=True, default=timezone.now())
    comment_check = models.BooleanField(default=True)
    publish_check = models.BooleanField(default=False)
    status = models.CharField(default='DRAFT', max_length=100, choices=POST_TYPE)
    published_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        post_urn_list = ", ".join(str(org) for org in self.post_urn.all())
        return f"{self.post} - Post To: {post_urn_list}"


class SharePage(models.Model):


    org_id = models.CharField(max_length=1000, blank=True)
    name = models.CharField(max_length=1000, blank=True)
    provider = models.CharField(max_length=255, blank=True)
    access_token = models.CharField(max_length=500, blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)


    def __str__(self):
        return self.name


class Post_urn(models.Model):
    org = models.ForeignKey(SharePage, on_delete=models.CASCADE)
    urn = models.CharField(max_length=600, blank=True)
    post_likes = models.IntegerField(default=0)
    post_comments = models.IntegerField(default=0)
    comments = models.CharField(max_length=2500, blank=True)
    is_liked = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.org.name + "--" + self.urn


class SocialStats(BaseModel):
    org = models.ForeignKey(SharePage, on_delete=models.CASCADE)
    t_likes = models.IntegerField(default=0)
    t_comments = models.IntegerField(default=0)
    t_followers = models.IntegerField(default=0)
    date = models.DateTimeField()


    def __str__(self):
        return self.org.name + "--" + self.date.__str__()

# class CeleryTask(models.Model):
#     STATUS_TYPE = [("FINISHED","FINISHED"), ('PROCESSING', 'PROCESSING'), ('FAILED', 'FAILED')]
#
#     task_id = models.CharField()
#     status = models.CharField(default='PROCESSING', max_length=100,choices = STATUS_TYPE)

