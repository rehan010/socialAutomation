from rest_framework import serializers
from .models import User, ImageModel, InviteEmploye, PostModel, SharePage,Post_urn

class UserGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','email','first_name','last_name','username','profile_image']
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

class SharePageSerializer(serializers.ModelSerializer):
    class Meta:
        model = SharePage
        fields = '__all__'

class PosturnSerializer(serializers.ModelSerializer):
    org = SharePageSerializer()
    class Meta:
        model = Post_urn
        fields = '__all__'

class PostSerializer(serializers.ModelSerializer):
    post_urn = PosturnSerializer(many=True)
    images = PostImageSerializer(many=True)
    prepost_page = SharePageSerializer(many=True)
    user = UserGetSerializer()

    class Meta:
        model = PostModel
        fields = ['id','post','post_urn','prepost_page','created_at','published_at','images','status','user','schedule_datetime']
