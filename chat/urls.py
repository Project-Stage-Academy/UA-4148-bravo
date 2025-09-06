from django.urls import path
from chat.views import ConversationCreateView, SendMessageView, ConversationMessagesView

urlpatterns = [
    path("conversations/", ConversationCreateView.as_view(), name="create_conversation"),
    path("messages/", SendMessageView.as_view(), name="send_message"),
    path("conversations/<str:room_name>/messages/", ConversationMessagesView.as_view(), name="list_messages"),
]
