import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.cache import cache
from .models import Document, DocumentVersion
from django.contrib.auth import get_user_model

User = get_user_model()

class DocumentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.document_id = self.scope['url_route']['kwargs']['document_id']
        self.room_group_name = f'document_{self.document_id}'
        self.user = self.scope['user']

        # 加入房间组
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # 将用户添加到活跃用户列表
        await self.add_active_user()
        
        await self.accept()
        
        # 广播用户加入消息
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_join',
                'user_id': self.user.id,
                'username': self.user.username
            }
        )

    async def disconnect(self, close_code):
        # 从房间组中移除
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        # 将用户从活跃用户列表中移除
        await self.remove_active_user()
        
        # 广播用户离开消息
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_leave',
                'user_id': self.user.id,
                'username': self.user.username
            }
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')

        if message_type == 'cursor_position':
            await self.handle_cursor_position(data)
        elif message_type == 'content_change':
            await self.handle_content_change(data)
        elif message_type == 'selection_change':
            await self.handle_selection_change(data)

    async def handle_cursor_position(self, data):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'cursor_position_update',
                'user_id': self.user.id,
                'username': self.user.username,
                'position': data['position']
            }
        )

    async def handle_content_change(self, data):
        # 保存文档变更
        await self.save_document_change(data['content'])
        
        # 广播变更
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'content_change_update',
                'user_id': self.user.id,
                'username': self.user.username,
                'content': data['content'],
                'delta': data.get('delta', {})
            }
        )

    async def handle_selection_change(self, data):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'selection_change_update',
                'user_id': self.user.id,
                'username': self.user.username,
                'selection': data['selection']
            }
        )

    async def cursor_position_update(self, event):
        await self.send(text_data=json.dumps(event))

    async def content_change_update(self, event):
        await self.send(text_data=json.dumps(event))

    async def selection_change_update(self, event):
        await self.send(text_data=json.dumps(event))

    async def user_join(self, event):
        await self.send(text_data=json.dumps(event))

    async def user_leave(self, event):
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def save_document_change(self, content):
        document = Document.objects.get(id=self.document_id)
        document.content = content
        document.save()
        
        # 创建新的版本记录
        DocumentVersion.objects.create(
            document=document,
            content=content,
            created_by=self.user
        )

    @database_sync_to_async
    def add_active_user(self):
        cache_key = f'document_{self.document_id}_users'
        active_users = cache.get(cache_key, set())
        active_users.add(self.user.id)
        cache.set(cache_key, active_users)

    @database_sync_to_async
    def remove_active_user(self):
        cache_key = f'document_{self.document_id}_users'
        active_users = cache.get(cache_key, set())
        active_users.discard(self.user.id)
        cache.set(cache_key, active_users)
