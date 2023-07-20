from allauth.socialaccount.models import SocialAccount
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
User = get_user_model()

# Create your models here.


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


class PointFileModel(BaseModel):
    name = models.CharField(max_length=255, blank=True)
    point_file = models.FileField(upload_to='point_file')
    user = models.ForeignKey(User, on_delete=models.CASCADE,null=True,blank=True)


class LatLongModel(BaseModel):
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    file = models.ForeignKey(PointFileModel, on_delete=models.CASCADE,null=True,blank=True)

    def __str__(self):
        return f"Latitude: {self.latitude}, Longitude: {self.longitude}"


class ImageModel(models.Model):
    image = models.FileField(upload_to='videos/')
    image_urn = models.CharField(max_length=255, blank=True)
    image_posted = models.CharField(max_length=500,blank=True,null=True)
    image_url = models.CharField(max_length=1000,blank=True,null=True)

    def is_mp4_file(self):
        file_extension = self.image.name.split('.')[-1].lower()
        return file_extension == 'mp4'

class PostModel(BaseModel):
    POST_TYPE = [('DRAFT', 'DRAFT'), ('PUBLISHED', 'PUBLISHED'),('SCHEDULED', 'SCHEDULED')]
    post = models.TextField(blank=True)
    images = models.ManyToManyField('ImageModel')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True,blank=True)
    post_urn = models.ManyToManyField('Post_urn')
    prepost_page = models.ManyToManyField('SharePage')
    comment_check = models.BooleanField(default=True)
    publish_check = models.BooleanField(default=False)
    status = models.CharField(default='DRAFT', max_length=100, choices=POST_TYPE)


    def __str__(self):
        post_urn_list = ", ".join(str(org) for org in self.post_urn.all())
        return f"{self.post} - Post To: {post_urn_list}"

    # def publish(self):
    #     # Logic for immediate publishing
    #     self.published_date = timezone.now()
    #     self.save()
    #
    # def schedule(self, scheduled_date):
    #     # Logic for scheduling the post
    #     scheduled_post = ScheduledPost.objects.create(post=self, scheduled_date=scheduled_date)
    #     return scheduled_post



class SharePage(models.Model):
    org_id = models.CharField(max_length=1000, blank=True)
    name = models.CharField(max_length=1000, blank=True)
    provider = models.CharField(max_length=255, blank=True)
    access_token = models.CharField(max_length=500, blank=True,null=True)
    user = models.ForeignKey(SocialAccount, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Post_urn(models.Model):
    org = models.ForeignKey(SharePage, on_delete=models.CASCADE)
    urn = models.CharField(max_length=600, blank=True)
    post_likes = models.IntegerField(default=0)
    post_comments = models.IntegerField(default=0)
    comments = models.CharField(max_length=2500, blank=True)

    def __str__(self):
        return self.org.name + "--" + self.urn


# class ScheduledPost(models.Model):
#     post = models.ForeignKey(PostModel, on_delete=models.CASCADE)
#     scheduled_date = models.DateTimeField()