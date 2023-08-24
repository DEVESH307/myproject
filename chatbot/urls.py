from django.urls import path
from . import views

urlpatterns = [
    path('', views.chatbot_view, name='chatbot'),
    path('bot-reply/', views.GetBotReplyAPIView.as_view(), name='get_bot_reply'),
    # path('bot-reply/conversational/', views.conversational_chatbot, name='conversational_chatbot'),
    # path('bot-reply/rule-based/', views.rule_based_chatbot, name='rule_based_chatbot'),
]
