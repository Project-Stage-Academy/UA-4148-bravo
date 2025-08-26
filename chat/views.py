from django.shortcuts import render
from django.conf import settings
from django.http import JsonResponse


def index(request):
    return render(request, "chat/index.html")


def room(request, room_name):
    return render(request, "chat/room.html", {"room_name": room_name})


def chat_config(request):
    return JsonResponse({
        "MAX_MESSAGE_LENGTH": 1000,
        "FORBIDDEN_WORDS": getattr(settings, "FORBIDDEN_WORDS_SET", []),
    })
