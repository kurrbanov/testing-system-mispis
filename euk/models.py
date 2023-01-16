from django.db import models
from django.core.validators import MinValueValidator


class Section(models.Model):
    title = models.CharField(max_length=255, verbose_name="Название раздела")

    def __str__(self):
        return f"{self.title}"

    class Meta:
        verbose_name = "Раздел"
        verbose_name_plural = "Разделы"


class Topic(models.Model):
    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        verbose_name="Раздел",
    )
    title = models.CharField(max_length=255, verbose_name="Название темы")

    def __str__(self):
        return f"{self.title}"

    class Meta:
        verbose_name = "Тема"
        verbose_name_plural = "Темы"


class CustomUser(models.Model):
    id = models.IntegerField(
        primary_key=True,
        unique=True,
        verbose_name="№ Зачётной книжки",
    )
    name = models.CharField(max_length=255, verbose_name="Фамилия и имя")
    password = models.TextField(verbose_name="Пароль")
    uuid = models.TextField(verbose_name="UUID текущей сессии", null=True)

    def __str__(self):
        return f"{self.name}, {self.id}"

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"


class Test(models.Model):
    class TestType(models.TextChoices):
        THEORY = "THEORY", "Теория"
        METHODOLOGY = "METHODOLOGY", "Методология"
        LEARNING_PROBLEM = "LEARNING_PROBLEM", "Учебные проблемы"

    type = models.CharField(max_length=20, choices=TestType.choices)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, verbose_name="Тема")

    def __str__(self):
        return f"{self.topic} - {Test.TestType[self.type].label}"

    class Meta:
        verbose_name = "Тест"
        verbose_name_plural = "Тесты"


class Question(models.Model):
    class Level(models.TextChoices):
        EASY = "EASY", "Лёгкий"
        MEDIUM = "MEDIUM", "Средний"
        HARD = "HARD", "Сложный"

    class Type(models.TextChoices):
        TEXT = "TEXT", "Текстовый"
        OPTION = "OPTION", "Вариативный"

    id = models.AutoField(primary_key=True)
    test = models.ForeignKey(Test, on_delete=models.CASCADE, verbose_name="Тест")
    title = models.CharField(max_length=255, verbose_name="Вопрос")
    image = models.ImageField(
        blank=True,
        null=True,
        verbose_name="Картинка к вопросу",
    )
    time = models.IntegerField(
        verbose_name="Время в секундах",
        validators=[MinValueValidator(5)],
    )
    level = models.CharField(
        max_length=10,
        choices=Level.choices,
        verbose_name="Сложность",
    )
    type = models.CharField(
        max_length=15,
        choices=Type.choices,
        verbose_name="Тип вопроса",
    )

    def __str__(self):
        return f"{self.title[:20]}"

    class Meta:
        verbose_name = "Вопрос"
        verbose_name_plural = "Вопросы"


class TextQuestion(models.Model):
    question = models.OneToOneField(
        Question,
        to_field='id',
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='text_question',
    )
    answer = models.TextField(verbose_name="Правильный ответ")

    def __str__(self):
        return f"{self.question.title[:25]}"

    class Meta:
        verbose_name = "Текстовый вопрос"
        verbose_name_plural = "Текстовые вопросы"


class OptionQuestion(models.Model):
    question = models.OneToOneField(
        Question,
        to_field='id',
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='option_question',
    )
    variant_1 = models.CharField(max_length=255, verbose_name="Вариант №1")
    variant_2 = models.CharField(max_length=255, verbose_name="Вариант №2")
    variant_3 = models.CharField(max_length=255, verbose_name="Вариант №3")
    variant_4 = models.CharField(max_length=255, verbose_name="Вариант №4")
    answer = models.IntegerField(verbose_name="Правильный вариант")

    def __str__(self):
        return f"{self.question.title[:25]}"

    class Meta:
        verbose_name = "Вариативный вопрос"
        verbose_name_plural = "Вариативные вопросы"


class TestUser(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, verbose_name="Тест")
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
    )
    time_start = models.DateTimeField(verbose_name="Время начала")
    time_end = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Время окончания",
    )

    def __str__(self):
        return f"{self.user} - {self.test}"

    class Meta:
        verbose_name = "Тест пользователя"
        verbose_name_plural = "Тесты пользователя"


class UserAnswer(models.Model):
    class Type(models.TextChoices):
        TEXT = "TEXT", "Текстовый"
        OPTION = "OPTION", "Вариативный"

    test_user = models.ForeignKey(
        TestUser,
        on_delete=models.CASCADE,
        verbose_name="Тест пользователя",
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        verbose_name="Вопрос",
    )
    answer = models.TextField(verbose_name="Ответ", null=True)
    type = models.CharField(
        max_length=15,
        choices=Type.choices,
        verbose_name="Тип вопроса",
    )
    time = models.DateTimeField(
        verbose_name="Время ответа",
    )

    def __str__(self):
        return f"{self.question[:15]} - {self.answer}"

    class Meta:
        verbose_name = "Ответ пользователя"
        verbose_name_plural = "Ответы пользователя"
