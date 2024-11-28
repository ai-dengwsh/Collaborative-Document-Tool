from rest_framework_nested import routers
from django.urls import path, include
from . import views

router = routers.DefaultRouter()
router.register(r'documents', views.DocumentViewSet)

documents_router = routers.NestedDefaultRouter(router, r'documents', lookup='document')
documents_router.register(r'versions', views.DocumentVersionViewSet, basename='document-versions')
documents_router.register(r'permissions', views.DocumentPermissionViewSet, basename='document-permissions')
documents_router.register(r'shares', views.DocumentShareViewSet, basename='document-shares')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(documents_router.urls)),
]
