from rest_framework import serializers
from .models import User,ImageModel

class UserGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

class PostImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageModel
        fields = '__all__'
