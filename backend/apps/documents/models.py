from django.db import models
from django.contrib.auth.models import User


class Document(models.Model):
    """文档模型"""
    title = models.CharField(max_length=255, verbose_name="标题")
    content = models.JSONField(default=dict, verbose_name="内容")
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents', verbose_name="所有者")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    is_deleted = models.BooleanField(default=False, verbose_name="是否删除")

    class Meta:
        verbose_name = "文档"
        verbose_name_plural = verbose_name
        ordering = ['-updated_at']

    def __str__(self):
        return self.title


class DocumentVersion(models.Model):
    """文档版本模型"""
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='versions', verbose_name="文档")
    content = models.JSONField(verbose_name="内容")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="创建者")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    version_number = models.PositiveIntegerField(verbose_name="版本号")

    class Meta:
        verbose_name = "文档版本"
        verbose_name_plural = verbose_name
        ordering = ['-version_number']
        unique_together = ['document', 'version_number']

    def __str__(self):
        return f"{self.document.title} - v{self.version_number}"


class DocumentPermission(models.Model):
    """文档权限模型"""
    PERMISSION_CHOICES = [
        ('view', '查看'),
        ('edit', '编辑'),
        ('admin', '管理'),
    ]

    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='permissions', verbose_name="文档")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='document_permissions', verbose_name="用户")
    permission = models.CharField(max_length=10, choices=PERMISSION_CHOICES, verbose_name="权限")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        verbose_name = "文档权限"
        verbose_name_plural = verbose_name
        unique_together = ['document', 'user']

    def __str__(self):
        return f"{self.document.title} - {self.user.username} - {self.get_permission_display()}"


class DocumentShare(models.Model):
    """文档分享模型"""
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='shares', verbose_name="文档")
    share_token = models.CharField(max_length=100, unique=True, verbose_name="分享令牌")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shared_documents', verbose_name="创建者")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name="过期时间")
    is_password_protected = models.BooleanField(default=False, verbose_name="是否密码保护")
    password_hash = models.CharField(max_length=255, null=True, blank=True, verbose_name="密码哈希")

    class Meta:
        verbose_name = "文档分享"
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.document.title} - {self.share_token}"
