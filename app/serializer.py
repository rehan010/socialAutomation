from rest_framework import serializers
from .models import User,ImageModel,InviteEmploye,PostModel

class UserGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'
class InviteSerializer(serializers.ModelSerializer):
    class Meta:
        model = InviteEmploye
        fields = '__all__'

class CombinedSerializer(serializers.Serializer):
    user_data = UserGetSerializer(many=True)
    invite_data = InviteSerializer(many=True)

class PostImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageModel
        fields = '__all__'


class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostModel
        fields = '__all__'
