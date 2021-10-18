from django.contrib.auth import get_user_model
from rest_framework import serializers

from core.models import User as UserModel

User: UserModel = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('email', 'password', 'name')
        extra_kwargs = {
            'password': {
                'write_only': True,
                'min_length': 5
            }
        }

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)
