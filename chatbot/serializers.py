from rest_framework import serializers

class MessageSerializer(serializers.Serializer):
    message = serializers.CharField()
    is_user = serializers.BooleanField(default=True)
