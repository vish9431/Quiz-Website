from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.models import User, auth
from django.contrib import messages
from .models import LearnerProfile, QuizRecord, RatingLog
from instructor.models import QuizPost, LiveTime, InstructorProfile
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import logout
from django.utils import timezone

import json
import os
from datetime import datetime
import requests
from random import shuffle
from questgen.work import generate_quest
import html
from math import ceil


def learner_check(user):
    if user.id:
        if LearnerProfile.objects.filter(user=user).exists():
            return True
        else:
            return False
    return False


def signin(response):
    if response.method == 'POST':
        username = response.POST['username']
        password = response.POST['password']

        user = auth.authenticate(username=username, password=password)

        if user is not None:
            if LearnerProfile.objects.filter(user=User.objects.get(username=username)).exists():
                auth.login(response, user)
                return redirect('/learner/my-profile')
            else:
                return HttpResponse('Login as Instructor!!!!!')
        else:
            messages.info(response, 'Invalid credentials')
            return redirect('signin')
    else:
        return render(response, 'learner/signin.html')


def signup(response):
    if response.method == 'POST':
        username = response.POST['reg-username']
        email = response.POST['reg-email']
        password1 = response.POST['reg-password1']
        password2 = response.POST['reg-password2']

        if password1 == password2:
            if User.objects.filter(email=email).exists():
                messages.info(response, 'Email taken')
                return redirect('signup')
            elif User.objects.filter(username=username).exists():
                messages.info(response, 'Username taken')
                return redirect('signup')
            else:
                user = User.objects.create_user(username=username, email=email, password=password1)
                user.save()

                user_login = auth.authenticate(username=username, password=password1)
                auth.login(response, user_login)

                user_model = User.objects.get(username=username)
                new_profile = LearnerProfile.objects.create(user=user_model, id_user=user_model.id, rating=1000)
                new_profile.save()

                rating_log = RatingLog.objects.create(user=username, rating=1000, affect_on=timezone.now())
                rating_log.save()

                os.makedirs(f'learner-profiles/{username}')

                return redirect('/learner/my-profile')
        else:
            messages.info(response, 'Password not matching')

    return render(response, 'learner/signin.html')


@user_passes_test(learner_check, login_url='/learner/signin')
def my_account(response):
    user = response.user
    profile = LearnerProfile.objects.get(user=user)

    rating_ls = RatingLog.objects.filter(user=user.username).order_by('-affect_on')[:10]
    rating_ls = list(rating_ls.values_list('rating', flat=True))
    rating_ls.reverse()

    if response.method == 'POST':
        if response.POST.get('submit'):
            name = response.POST['name']
            phone_num = response.POST['pnum']
            dob = response.POST['dob']
            bio = response.POST['bio']
            gender = response.POST['gender']

            profile.name = name
            profile.phone_num = phone_num
            profile.dob = dob
            profile.bio = bio
            profile.gender = gender
            profile.save()

            return redirect('learner-profile')

        elif response.POST.get('save'):
            if response.POST['current-pass'] == user.password:
                if response.POST['new-pass'] == response.POST['confirm-pass']:
                    user.set_password(response.POST['new-pass'])
                    user.save()
                else:
                    messages.info(response, 'Passwords does not match!!!')
            else:
                messages.info(response, 'Current password is wrong!!!')

            return redirect('learner-profile')

    return render(response, 'learner/profile.html', {'profile': profile, 'user': user,
                                                     'rating': rating_ls, 'labels': ['' for _ in rating_ls]})


@user_passes_test(learner_check, login_url='/learner/signin')
def quiz_list(response):
    user = response.user.username
    ls = QuizRecord.objects.filter(user=user).all()

    quiz_ls = []
    for quiz in ls:
        quiz_ls.append(QuizPost.objects.get(id=quiz.id_quiz))

    return render(response, 'learner/quiz-list.html', {'quiz_ls': quiz_ls})


@user_passes_test(learner_check, login_url='/learner/signin')
def take_quiz(response):
    quiz_id = response.GET.get('quiz_id')
    quiz_model = QuizPost.objects.get(id=quiz_id)

    time_allot = quiz_model.time_allot
    ls = []
    for _ in range(3):
        ls.append(int(time_allot % 10))
        time_allot = time_allot // 10

    if response.method == 'POST':
        with open(f"quiz-data/{quiz_id}.txt") as file:
            quiz_set = json.load(file)

        if response.POST.get('submit'):
            user = response.user.username

            correct_count = 0
            wrong_count = 0
            score = 0

            data = quiz_set.copy()
            for i in range(1, quiz_model.number + 1):
                data[i - 1]['user'] = response.POST.get(f'options-{i}')
                if response.POST.get(f'options-{i}'):
                    if response.POST.get(f'options-{i}') == quiz_set[i - 1]['correct']:
                        correct_count += 1
                        score += int(quiz_set[i - 1]['mark'])
                    else:
                        wrong_count += 1

            with open(f'learner-profiles/{user}/{quiz_id}.txt', 'w') as file:
                json.dump(data, file)

            time_taken = 60 * int(quiz_model.time_allot) - (60 * int(response.session['m']) + int(response.session['s']))
            print(time_taken)
            rating_diff = calculate_rating(quiz_model.difficulty, time_taken / (60 * quiz_model.time_allot),
                                           score / quiz_model.total_marks)

            if QuizRecord.objects.filter(id_quiz=quiz_id, user=user).exists():
                records = QuizRecord.objects.filter(id_quiz=quiz_id, user=user).all()
                for record in records:
                    record.delete()

            record_model = QuizRecord.objects.create(id_quiz=quiz_id, user=user, score=score,
                                                     correct=correct_count, incorrect=wrong_count,
                                                     total=quiz_model.number, rating_diff=rating_diff,
                                                     time_taken=time_taken)
            record_model.save()

            quiz_model.attempt_count += 1
            quiz_model.save()

            learner_model = LearnerProfile.objects.get(user=response.user)
            learner_model.rating += rating_diff
            learner_model.save()

            rating_model = RatingLog.objects.create(user=user, rating=learner_model.rating, affect_on=timezone.now())
            rating_model.save()

            return redirect(f'/learner/quiz-result?quiz_id={quiz_id}')

        else:

            if quiz_model.live:
                model = LiveTime.objects.get(id=quiz_id)
                if timezone.now() > model.close_time or timezone.now() < model.start_time:
                    return HttpResponse('Not Available')

            data = {
                'count': range(quiz_model.number),
                't': ls,
                'set': quiz_set,
                'model': quiz_model,
            }

            return render(response, 'learner/quiz.html', data)

    if quiz_model.live:
        model = LiveTime.objects.get(id=quiz_id)
    else:
        model = None

    return render(response, 'learner/quiz-intro.html',
                  {'model': quiz_model, 'count': range(1, quiz_model.number + 1), 't': ls, 'live': model})


@user_passes_test(learner_check, login_url='/learner/signin')
def result_page(response):
    quiz_id = response.GET.get('quiz_id')
    user = response.user.username

    record_model = QuizRecord.objects.get(user=user, id_quiz=quiz_id)
    quiz_model = QuizPost.objects.get(id=quiz_id)

    time_taken = str(record_model.time_taken // 60) + ':' + str(record_model.time_taken % 60)

    lead_records = QuizRecord.objects.filter(id_quiz=quiz_id).order_by('-score')[:10]

    return render(response, 'learner/quiz-result.html', {'model': record_model, 'quiz': quiz_model,
                                                         'time_taken': time_taken, 'records': lead_records})


@user_passes_test(learner_check, login_url='/learner/signin')
def review_page(response):
    quiz_id = response.GET.get('quiz_id')
    user = response.user.username
    model = QuizPost.objects.get(id=quiz_id)

    with open(f'learner-profiles/{user}/{quiz_id}.txt') as file:
        data = json.load(file)

    return render(response, 'learner/quiz-review.html', {'data': data, 'model': model})


@user_passes_test(learner_check, login_url='/learner/signin')
def live_list(response):
    q = []
    ls = []
    for model in LiveTime.objects.all():

        if model.start_time < timezone.now() < model.close_time:
            q.append(QuizPost.objects.get(id=model.id))
            ls.append(model)

    return render(response, 'learner/quiz-all.html', {'quiz_ls': q})


@user_passes_test(learner_check, login_url='/learner/signin')
def countdown(response):
    if response.method == 'POST':
        print(response.POST['m'])
        m = int(response.POST['m'])
        s = int(response.POST['s'])

        response.session['m'] = m
        response.session['s'] = s

        data = {'sub': False}
        if m == 0 and s == 0:
            return HttpResponse(json.dumps({'sub': True}), content_type='application/json')
        elif s == 0:
            m -= 1
            s = 59
            data['m_100'] = m // 100
            data['m_10'] = (m // 10) % 10
            data['m_1'] = m % 10
            data['s_10'] = 5
            data['s_1'] = 9
        else:
            data['m_100'] = m // 100
            data['m_10'] = (m // 10) % 10
            data['m_1'] = m % 10
            if s <= 10:
                data['s_10'] = 0
                data['s_1'] = s - 1
            else:
                data['s_10'] = (s - 1) // 10
                data['s_1'] = (s - 1) % 10

        return HttpResponse(json.dumps(data), content_type='application/json')


@user_passes_test(learner_check, login_url='/learner/signin')
def all_quiz(response):
    quiz_ls = QuizPost.objects.filter(live=False)

    return render(response, 'learner/quiz-all.html', {'quiz_ls': quiz_ls})


def calculate_rating(diff, t_ratio, s_ratio):
    k = s_ratio / t_ratio

    if diff == 'easy':
        if k == 0:
            rating = -20
        elif k < 0.4:
            rating = -20 * (1 - k)
        else:
            rating = 20 * k

        if rating > 20:
            rating = 20
    elif diff == 'medium':
        if k == 0:
            rating = -25
        elif k < 0.35:
            rating = -25 * (1 - k)
        else:
            rating = 25 * k

        if rating > 25:
            rating = 25
    elif diff == 'hard':
        if k == 0:
            rating = -30
        elif k < 0.3:
            rating = -30 * (1 - k)
        else:
            rating = 30 * k

        if rating > 30:
            rating = 30
    else:
        rating = 0

    return ceil(rating)


@user_passes_test(learner_check, login_url='/learner/signin')
def practice_quiz(response):
    if response.method == 'POST':
        if response.POST.get('start'):
            count = int(response.POST['count'])
            cat = int(response.POST['category'])
            diff = response.POST['difficulty']

            if cat != -1 and diff != 'any':
                quiz_set = requests.get(
                    url=f'https://opentdb.com/api.php?amount={count}&category={cat}&difficulty={diff}&type=multiple')
                if len(quiz_set.json()['results']) < count:
                    quiz_set = requests.get(
                        url=f'https://opentdb.com/api.php?amount={count}&category={cat}&type=multiple')
            elif cat == -1 and diff != 'any':
                quiz_set = requests.get(
                    url=f'https://opentdb.com/api.php?amount={count}&difficulty={diff}&type=multiple')
            elif cat != -1 and diff == 'any':
                quiz_set = requests.get(
                    url=f'https://opentdb.com/api.php?amount={count}&category={cat}&type=multiple')
            else:
                quiz_set = requests.get(
                    url=f'https://opentdb.com/api.php?amount={count}&type=multiple')

            quiz_set = quiz_set.json()['results']
            for i in quiz_set:
                i['question'] = html.unescape(i['question'])
                i['options'] = i['incorrect_answers']
                i['options'].append(i['correct_answer'])
                shuffle(i['options'])

            response.session['quiz_set'] = quiz_set

            return render(response, 'learner/practice-quiz.html', {'data': quiz_set})
        else:
            quiz_set = response.session['quiz_set']
            correct_answers = []
            for i in quiz_set:
                correct_answers.append(i['correct_answer'])

            data = {
                'count': len(correct_answers),
                'answers': correct_answers
            }

            return HttpResponse(json.dumps(data), content_type='application/json')

    return render(response, 'learner/practice-intro.html')


@user_passes_test(learner_check, login_url='/learner/signin')
def generate(response):
    if response.method == 'POST':
        quest_set = response.session['quiz_set']
        correct_answers = []
        for i in quest_set:
            correct_answers.append(i['answer'])

        data = {
            'count': len(correct_answers),
            'answers': correct_answers
        }

        return HttpResponse(json.dumps(data), content_type='application/json')

    src = response.GET.get('src')
    keyword = response.GET.get('q')

    if src == 'wiki':
        s = 'Wikipedia'
    else:
        s = 'Custom Link'

    quest_set = generate_quest(keyword, src)
    if quest_set is not None:
        if len(quest_set) > 0:
            response.session['quiz_set'] = quest_set

            return render(response, 'learner/generated-quiz.html', {'data': quest_set, 'src': s})
        else:
            return render(response, 'learner/error.html', {'error': 'Not able to gather questions!!!!'})


@user_passes_test(learner_check, login_url='/learner/signin')
def instructor_list(response):
    instructors = InstructorProfile.objects.all()

    return render(response, 'learner/instructor-list.html', {'data': instructors})


@user_passes_test(learner_check, login_url='/learner/signin')
def instructor_profile(response):
    username = response.GET.get('user')
    user = User.objects.get(username=username)

    profile = InstructorProfile.objects.get(user=user)
    return render(response, 'learner/instructor-profile.html', {'data': profile})


@user_passes_test(learner_check, login_url='/learner/signin')
def home_page(response):
    return render(response, 'learner/index.html')


@user_passes_test(learner_check, login_url='/learner/signin')
def logout_l(response):
    logout(response)

    return redirect('/')
