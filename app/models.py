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
    post= models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE,null=True,blank=True)



