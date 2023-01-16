from decimal import Decimal

from django.db import transaction
from django.db.models import Q
from django.http import QueryDict
from django.shortcuts import render, reverse
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from django.http import HttpRequest, HttpResponseRedirect

from euk.utils import (
    check_login,
    set_uuid,
    today_msk,
    get_user,
    level_mapping,
)
from euk.forms import RegisterForm
from euk.models import (
    CustomUser,
    Section,
    Topic,
    Test,
    Question,
    TextQuestion,
    OptionQuestion,
    TestUser,
    UserAnswer,
)


class RegisterView(View):
    @staticmethod
    def get(request: HttpRequest):
        return render(request, "register.html")

    @staticmethod
    def post(request):
        form = RegisterForm(request.POST)
        if form.is_valid():
            custom_user: CustomUser = form.save(commit=False)
            custom_user.password = make_password(request.POST.get("password"))
            set_uuid(custom_user, request)
            custom_user.save()
            return HttpResponseRedirect(reverse("main-page"))
        if form.errors.get("id"):
            messages.add_message(request, messages.ERROR, form.errors.get("id").as_text())
        if form.errors.get("name"):
            messages.add_message(request, messages.ERROR, form.errors.get("name").as_text())
        if form.errors.get("password"):
            messages.add_message(request, messages.ERROR, form.errors.get("password").as_text())
        return render(request, "register.html")


class LoginView(View):
    @staticmethod
    def get(request):
        return render(request, "login.html")

    @staticmethod
    def post(request):
        id_ = request.POST.get("id")
        password = request.POST.get("password")
        custom_user = CustomUser.objects.filter(id=id_).first()
        if custom_user:
            if check_password(password, custom_user.password):
                set_uuid(custom_user, request)
                return HttpResponseRedirect(reverse("main-page"))
        messages.add_message(request, messages.ERROR, "Неверные данные.")
        return render(request, "login.html")


@method_decorator(check_login, name="dispatch")
class LogoutView(View):
    @staticmethod
    def get(request: HttpRequest):
        custom_user = get_user(request)
        try:
            del request.session["session_id"]
        except KeyError:
            pass
        finally:
            custom_user.uuid = None
            custom_user.save()
        return HttpResponseRedirect(reverse("login"))


@method_decorator(check_login, name="dispatch")
class MainPage(View):
    @staticmethod
    def get(request):
        sections = Section.objects.all()
        custom_user = get_user(request)
        context = {
            "sections": sections,
            "custom_user": custom_user,
        }
        return render(request, "index.html", context=context)


@method_decorator(check_login, name="dispatch")
class SectionView(View):
    @staticmethod
    def get(request, pk: int):
        section = Section.objects.get(id=pk)
        topics = Topic.objects.filter(section=section)
        context = {
            "section": section,
            "topics": topics,
        }
        return render(request, "section.html", context=context)


@method_decorator(check_login, name="dispatch")
class TopicView(View):
    def get(self, request, pk: int):
        topic = Topic.objects.get(id=pk)
        user = get_user(request)
        context = {}
        (theory_test, methodology_test, learning_problem_test) = self.get_tests(topic)
        print(f"{learning_problem_test=}")
        if theory_test:
            theory_test_results = self.count_results(theory_test, user)
            context |= {"theory_test_results": theory_test_results}
        if methodology_test:
            methodology_test_results = self.count_results(methodology_test, user)
            context |= {"methodology_test_results": methodology_test_results}
        if learning_problem_test:
            learning_problem_test_results = self.count_results(learning_problem_test, user)
            context |= {"learning_problem_test_results": learning_problem_test_results}

        context |= {
            "topic": topic,
            "theory_test": theory_test,
            "methodology_test": methodology_test,
            "learning_problem_test": learning_problem_test,
        }
        return render(request, "topic.html", context=context)

    @staticmethod
    def count_results(test: Test, user: CustomUser):
        test_user = TestUser.objects.filter(Q(test=test)
                                            & Q(user=user)).first()
        if not test_user:
            return None
        user_answers = UserAnswer.objects.filter(
            test_user=test_user
        )
        level_map = level_mapping()
        cnt_percent: Decimal = Decimal(0.0)
        total_per_test: Decimal = Decimal(0.0)

        for user_answer in user_answers:
            if user_answer.type == UserAnswer.Type.TEXT:
                if (
                    user_answer.question.text_question.answer.lower()
                    == user_answer.answer.lower()
                ):
                    cnt_percent += Decimal(level_map[user_answer.question.level])
            else:
                if (
                    user_answer.question.option_question.answer
                    == int(user_answer.answer)
                ):
                    cnt_percent += Decimal(level_map[user_answer.question.level])

        for question in test_user.test.question_set.all():
            total_per_test += Decimal(level_map[question.level])

        return float(cnt_percent / total_per_test)

    @staticmethod
    def get_tests(topic: Topic):
        tests = Test.objects.filter(topic=topic)
        theory_test = tests.filter(type=Test.TestType.THEORY).first()
        methodology_test = tests.filter(type=Test.TestType.METHODOLOGY).first()
        learning_problem_test = tests.filter(type=Test.TestType.LEARNING_PROBLEM).first()
        return theory_test, methodology_test, learning_problem_test


@method_decorator(check_login, name="dispatch")
class RunTestView(View):
    @transaction.atomic()
    def get(self, request, pk: int):
        test = Test.objects.get(id=pk)
        user = get_user(request)
        if TestUser.objects.filter(
                Q(test=test)
                & Q(user=user)).exists():
            test_user = TestUser.objects.filter(
                Q(test=test)
                & Q(user=user)).first()
        else:
            test_user = TestUser.objects.create(
                test=test,
                user=user,
                time_start=today_msk(),
            )
            test_user.save()
        context = {
            "question": self.get_next_question(test_user=test_user),
        }
        return render(request, "question.html", context=context)

    @transaction.atomic()
    def post(self, request, pk: int):
        test = Test.objects.get(id=pk)
        user = get_user(request)
        test_user = TestUser.objects.filter(Q(test=test) & Q(user=user)).first()
        question_id = request.POST.get("question_id")
        question = Question.objects.get(id=int(question_id))
        if question.type == Question.Type.TEXT:
            user_answer = self.process_text_question(
                test_user, question, request.POST
            )
        else:
            user_answer = self.process_option_question(
                test_user, question, request.POST
            )

        if request.POST.get("submit_test"):
            test_user.time_end = user_answer.time
            test_user.save()
            return HttpResponseRedirect(reverse("topic", args=[test.topic_id]))

        context = {
            "question": self.get_next_question(test_user=test_user),
        }
        return render(request, "question.html", context=context)

    @staticmethod
    def process_text_question(
            test_user: TestUser,
            text_question: TextQuestion,
            data: QueryDict
    ):
        answer = data.get("answer")
        user_answer = UserAnswer.objects.create(
            test_user=test_user,
            question=text_question,
            answer=answer,
            type=UserAnswer.Type.TEXT,
            time=today_msk(),
        )
        user_answer.save()
        return user_answer

    @staticmethod
    def process_option_question(
            test_user: TestUser,
            option_question: OptionQuestion,
            data: QueryDict
    ):
        answer = None
        if data.get("variant_1") == "on":
            answer = 1
        elif data.get("variant_2") == "on":
            answer = 2
        elif data.get("variant_3") == "on":
            answer = 3
        elif data.get("variant_4") == "on":
            answer = 4

        user_answer = UserAnswer.objects.create(
            test_user=test_user,
            question=option_question,
            answer=answer,
            type=UserAnswer.Type.OPTION,
            time=today_msk(),
        )
        user_answer.save()
        return user_answer

    def get_next_question(self, test_user: TestUser):
        if self.check_level_passed(test_user, Question.Level.EASY):
            if self.check_level_passed(test_user, Question.Level.MEDIUM):
                if self.check_level_passed(test_user, Question.Level.HARD):
                    return None
                return self.get_random_question(test_user, Question.Level.HARD)
            return self.get_random_question(test_user, Question.Level.MEDIUM)
        return self.get_random_question(test_user, Question.Level.EASY)

    @staticmethod
    def check_level_passed(test_user: TestUser, level: Question.Level) -> bool:
        user_answers = list(UserAnswer.objects.filter(
            Q(test_user=test_user)
            & Q(question__level=level)
        ).values_list("question_id", flat=True))

        if level == Question.Level.EASY:
            return len(user_answers) == 1

        if level == Question.Level.MEDIUM:
            return len(user_answers) == 1

        if level == Question.Level.HARD:
            return len(user_answers) == 1

    @staticmethod
    def get_random_question(test_user: TestUser, level: Question.Level) -> Question:
        user_answers = list(UserAnswer.objects.filter(
            Q(test_user=test_user)
            & Q(question__level=level),
        ).values_list("question_id", flat=True))
        test = test_user.test.type
        print(f"{test_user.test.topic=}")
        print(f"{test_user=}")
        question = Question.objects.filter(
            Q(level=level)
            & ~Q(id__in=user_answers)
            & Q(test__topic=test_user.test.topic)
            & Q(test__type=test_user.test.type)
        ).order_by("?").first()
        print(f"{question=}")
        print(f"{question.test.topic=}")
        return question


@method_decorator(check_login, name="dispatch")
class BuildMapView(View):
    def get(self, request):
        user = get_user(request)
        internet = Topic.objects.get(title="Интернет")
        internet_tt, internet_mt, internet_lp = self.test_results(internet, user)
        internet_total = self.get_total_p([internet_tt, internet_mt, internet_lp])

        protocols = Topic.objects.get(title="Протоколы")
        protocols_tt, protocols_mt, protocols_lp = self.test_results(protocols, user)
        protocols_total = self.get_total_p([protocols_tt,  protocols_mt, protocols_lp])

        operators = Topic.objects.get(title="Операторы")
        operators_tt, operators_mt, operators_lp = self.test_results(operators, user)
        operators_total = self.get_total_p([operators_tt, operators_mt, operators_lp])

        optimizations = Topic.objects.get(title="Оптимизации")
        optimizations_tt, optimizations_mt, optimizations_lp = self.test_results(optimizations, user)
        optimizations_total = self.get_total_p([optimizations_tt, optimizations_mt, optimizations_lp])

        network_tt = (internet_tt + protocols_tt) / 2
        network_mt = (internet_mt + protocols_mt) / 2
        network_lp = protocols_lp

        db_tt = (operators_tt + optimizations_tt) / 2
        db_mt = (operators_mt + optimizations_mt) / 2
        db_lp = operators_lp

        tt = (network_tt + db_tt) / 2
        mt = (network_mt + db_mt) / 2
        lp = (network_lp + db_lp) / 2

        # syntax = Topic.objects.get(title="Синтаксис")
        # syntax_tt, syntax_mt, syntax_lp = self.test_results(syntax, user)
        # syntax_total = self.get_total_p([syntax_tt, syntax_mt, syntax_lp])
        #
        # sockets = Topic.objects.get(title="Работа с сокетами")
        # sockets_tt, sockets_mt, sockets_lp = self.test_results(sockets, user)
        # sockets_total = self.get_total_p([sockets_tt, sockets_mt, sockets_lp])
        #
        # multi = Topic.objects.get(title="Многопоточность")
        # multi_tt, multi_mt, multi_lp = self.test_results(multi, user)
        # multi_total = self.get_total_p([multi_tt, multi_mt, multi_lp])

        context = {
            "internet_tt": internet_tt,
            "internet_mt": internet_mt,
            "internet_lp": internet_lp,
            "protocols_tt": protocols_tt,
            "protocols_mt": protocols_mt,
            "protocols_lp": protocols_lp,
            "operators_tt": operators_tt,
            "operators_mt": operators_mt,
            "operators_lp": operators_lp,
            "optimizations_tt": optimizations_tt,
            "optimizations_mt": optimizations_mt,
            "optimizations_lp": optimizations_lp,
            # "syntax_tt": syntax_tt,
            # "syntax_mt": syntax_mt,
            # "syntax_lp": syntax_lp,
            # "sockets_tt": sockets_tt,
            # "sockets_mt": sockets_mt,
            # "sockets_lp": sockets_lp,
            # "multi_tt": multi_tt,
            # "multi_mt": multi_mt,
            # "multi_lp": multi_lp,
            "internet_total": internet_total,
            "protocols_total": protocols_total,
            "operators_total": operators_total,
            "optimizations_total": optimizations_total,
            "network_tt": network_tt,
            "network_mt": network_mt,
            "network_lp": network_lp,
            "db_tt": db_tt,
            "db_mt": db_mt,
            "db_lp": db_lp,
            "tt": tt,
            "mt": mt,
            "lp": lp,
            # "syntax_total": syntax_total,
            # "sockets_total": sockets_total,
            # "multi_total": multi_total,
            "comp_total": (internet_total + protocols_total) / 2,
            "db_total": (optimizations_total + operators_total) / 2,
            "common_total": (((internet_total + protocols_total) / 2) + ((optimizations_total + operators_total) / 2)) / 2
        }
        return render(request, "map.html", context=context)

    @staticmethod
    def test_results(topic: Topic, user: CustomUser):
        theory_test, methodology_test, lp_test = TopicView().get_tests(topic)

        tt_results, mt_results, lp_results = (None, None, None)

        if theory_test:
            tt_results = TopicView().count_results(theory_test, user)
        if methodology_test:
            mt_results = TopicView().count_results(methodology_test, user)
        if lp_test:
            lp_results = TopicView().count_results(lp_test, user)
        return tt_results, mt_results, lp_results

    @staticmethod
    def get_total_p(tests_results: list):
        tt, mt, lp = tests_results
        total = 0
        cnt = 0
        if tt:
            total += tt
            cnt += 1
        if mt:
            total += mt
            cnt += 1
        if lp:
            total += lp
            cnt += 1
        if cnt == 0:
            cnt += 1
        return total / cnt
