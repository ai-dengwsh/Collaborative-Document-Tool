from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Document, DocumentVersion, DocumentPermission, DocumentShare


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class DocumentSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    current_user_permission = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = ['id', 'title', 'content', 'owner', 'created_at', 'updated_at', 'current_user_permission']
        read_only_fields = ['owner', 'created_at', 'updated_at']

    def get_current_user_permission(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        
        if obj.owner == request.user:
            return 'admin'
        
        try:
            permission = obj.permissions.get(user=request.user)
            return permission.permission
        except DocumentPermission.DoesNotExist:
            return None


class DocumentVersionSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)

    class Meta:
        model = DocumentVersion
        fields = ['id', 'document', 'content', 'created_by', 'created_at', 'version_number']
        read_only_fields = ['created_by', 'created_at', 'version_number']


class DocumentPermissionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = DocumentPermission
        fields = ['id', 'document', 'user', 'user_id', 'permission', 'created_at']
        read_only_fields = ['created_at']

    def validate_user_id(self, value):
        try:
            User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User does not exist")
        return value


class DocumentShareSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = DocumentShare
        fields = ['id', 'document', 'share_token', 'created_by', 'created_at', 'expires_at',
                 'is_password_protected', 'password']
        read_only_fields = ['share_token', 'created_by', 'created_at']

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        share = super().create(validated_data)
        
        if password:
            share.is_password_protected = True
            share.password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            share.save()
        
        return share
