from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Document, DocumentVersion, DocumentPermission, DocumentShare
from .serializers import (
    DocumentSerializer, DocumentVersionSerializer,
    DocumentPermissionSerializer, DocumentShareSerializer
)


class IsOwnerOrHasPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if obj.owner == request.user:
            return True
        
        if isinstance(obj, Document):
            try:
                permission = obj.permissions.get(user=request.user)
                if request.method in permissions.SAFE_METHODS:
                    return permission.permission in ['view', 'edit', 'admin']
                return permission.permission in ['edit', 'admin']
            except DocumentPermission.DoesNotExist:
                return False
        
        return False


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.filter(is_deleted=False)
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrHasPermission]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save()

    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        document = self.get_object()
        document.is_deleted = False
        document.save()
        serializer = self.get_serializer(document)
        return Response(serializer.data)


class DocumentVersionViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentVersionSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrHasPermission]

    def get_queryset(self):
        return DocumentVersion.objects.filter(
            document_id=self.kwargs['document_pk']
        )

    def perform_create(self, serializer):
        document = get_object_or_404(Document, pk=self.kwargs['document_pk'])
        version_number = document.versions.count() + 1
        serializer.save(
            document=document,
            created_by=self.request.user,
            version_number=version_number
        )


class DocumentPermissionViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentPermissionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return DocumentPermission.objects.filter(
            document_id=self.kwargs['document_pk']
        )

    def perform_create(self, serializer):
        document = get_object_or_404(Document, pk=self.kwargs['document_pk'])
        if document.owner != self.request.user:
            try:
                permission = document.permissions.get(user=self.request.user)
                if permission.permission != 'admin':
                    raise permissions.PermissionDenied()
            except DocumentPermission.DoesNotExist:
                raise permissions.PermissionDenied()
        
        serializer.save(document=document)


class DocumentShareViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentShareSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return DocumentShare.objects.filter(
            document_id=self.kwargs['document_pk']
        )

    def perform_create(self, serializer):
        document = get_object_or_404(Document, pk=self.kwargs['document_pk'])
        if document.owner != self.request.user:
            try:
                permission = document.permissions.get(user=self.request.user)
                if permission.permission not in ['edit', 'admin']:
                    raise permissions.PermissionDenied()
            except DocumentPermission.DoesNotExist:
                raise permissions.PermissionDenied()
        
        serializer.save(
            document=document,
            created_by=self.request.user
        )
