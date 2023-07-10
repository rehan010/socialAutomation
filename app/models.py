from allauth.socialaccount.models import SocialAccount
from django.contrib.auth import get_user_model
from django.db import models

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


class PostModel(BaseModel):
    post = models.TextField(blank=True)
    file = models.FileField(upload_to='videos/', blank=True)
    post_urn = models.CharField(max_length=255, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE,null=True,blank=True)
    status = models.CharField(max_length=100,null=True)
    # post_likes = models.IntegerField(default=0)
    # post_comments = models.IntegerField(default=0)
    # comments = models.CharField(max_length=2500, blank=True)

class SharePage(BaseModel):
    user = models.ForeignKey(SocialAccount, on_delete=models.CASCADE)
    name = models.CharField(max_length=300,null=True)
    organizations_id = models.CharField(max_length=1000)
    access_token = models.CharField(max_length=1000,null=True)
    provider = models.CharField(max_length=100,null=True)
    post = models.ManyToManyField(PostModel)




