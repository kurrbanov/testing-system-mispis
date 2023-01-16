import zoneinfo

from datetime import datetime
from uuid import uuid4

from django.http import HttpResponseRedirect, HttpRequest
from django.shortcuts import reverse

from euk.models import CustomUser, Question


def check_login(func):
    def wrapper(request, pk=None):
        session_uuid = request.session.get("session_id")
        user = CustomUser.objects.filter(uuid=session_uuid).exists()
        if user:
            if pk:
                return func(request, pk)
            return func(request)
        return HttpResponseRedirect(reverse("login"))
    return wrapper


def set_uuid(custom_user: CustomUser, request: HttpRequest):
    uuid_value = str(uuid4())
    custom_user.uuid = uuid_value
    request.session["session_id"] = uuid_value
    request.session.set_expiry(60 * 60 * 24)
    custom_user.save()


def today_msk():
    zone = zoneinfo.ZoneInfo("Europe/Moscow")
    return datetime.now(zone)


def get_user(request):
    uuid_ = request.session.get("session_id")
    user = CustomUser.objects.filter(uuid=uuid_).first()
    return user


def level_mapping():
    return {
        Question.Level.EASY: 0.1,
        Question.Level.MEDIUM: 0.5,
        Question.Level.HARD: 1.1,
    }
