from django.forms import ModelForm
from django.core.exceptions import ValidationError

from euk.models import CustomUser


class RegisterForm(ModelForm):
    class Meta:
        model = CustomUser
        fields = ['id', 'name', 'password']

    def clean_id(self):
        value = str(self.cleaned_data.get("id"))
        if len(value) != 7:
            raise ValidationError("Количество цифр должно быть равно 7.")
        return value

    def clean_name(self):
        value = self.cleaned_data.get("name")
        if len(value) < 3:
            raise ValidationError("Имя слишком короткое.")
        return value

    def clean_password(self):
        value = self.cleaned_data.get("password")
        if len(value) < 6:
            raise ValidationError("Пароль слишком короткий.")
        return value
