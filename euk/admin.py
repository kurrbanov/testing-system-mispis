from django.contrib import admin

from euk.models import (
    CustomUser,
    Section,
    Topic,
    Test,
    Question,
    TextQuestion,
    OptionQuestion,
)


@admin.register(CustomUser)
class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    readonly_fields = ("id", "password", "uuid")


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ("id", "title")


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "section")

    @admin.display(description="Раздел")
    def section(self, obj: Topic):
        return obj.section.title


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ("id", "type", "topic")

    @admin.display(description="Тема")
    def topic(self, obj: Test):
        return obj.topic.title


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "test", "title", "image", "time", "level", "type")

    @admin.display(description="Тест")
    def test(self, obj: Question):
        return obj.test


@admin.register(TextQuestion)
class TextQuestionAdmin(admin.ModelAdmin):
    list_display = ("question", "answer")

    @admin.display(description="Вопрос")
    def question(self, obj: TextQuestion):
        return obj.question


@admin.register(OptionQuestion)
class OptionQuestionAdmin(admin.ModelAdmin):
    list_display = ("question", "answer")

    @admin.display(description="Вопрос")
    def question(self, obj: OptionQuestion):
        return obj.question


admin.site.site_header = "Курс по бекэнд-разработке"
admin.site.index_title = "Данные с курса"

