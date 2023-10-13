from django.shortcuts import render, redirect
from django.contrib.auth.models import User, auth
from django.contrib import messages
from .models import InstructorProfile, QuizPost, LiveTime, ContactRecord
from django.http import HttpResponse
from django.contrib.auth import logout
from django.contrib.auth.decorators import user_passes_test
from student.models import QuizRecord
from django.utils import timezone
from django.core.mail import send_mail, BadHeaderError

import json
from datetime import datetime


def instructor_check(user):
    if user.id:
        if InstructorProfile.objects.filter(user=user).exists():
            return True
        else:
            return False
    return False


def test(response):

    return render(response, 'instructor/base.html')


def signin(response):

    if response.method == 'POST':
        username = response.POST['username']
        password = response.POST['password']

        user = auth.authenticate(username=username, password=password)

        if user is not None:
            if InstructorProfile.objects.filter(user=User.objects.get(username=username)).exists():
                auth.login(response, user)
                return redirect('/instructor/my-profile')
            else:
                return HttpResponse('Login as Learner!!!!!')
        else:
            messages.info(response, 'Invalid credentials')
            return redirect('signin-i')
    else:
        return render(response, 'instructor/signin.html')


def signup(response):

    if response.method == 'POST':
        username = response.POST.get('reg-username')
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
                new_profile = InstructorProfile.objects.create(user=user_model, id_user=user_model.id)
                new_profile.save()

                return redirect('/instructor/my-profile')
        else:
            messages.info(response, 'Password not matching')

    return render(response, 'instructor/signin.html')


@user_passes_test(instructor_check, login_url='/instructor/signin')
def make_quiz(response):

    if response.method == 'POST':
        if response.POST.get('make'):
            count = int(response.POST['count'])
            runtime = int(response.POST['time'])
            tags = response.POST['tags']
            title = response.POST['title']
            difficulty = response.POST['difficulty']
            type_ = response.POST['type']
            description = response.POST['description']

            if type_ == 'live':
                response.session['start'] = response.POST['time_start']
                response.session['end'] = response.POST['time_end']

            response.session['count'] = count
            response.session['time'] = runtime
            response.session['tags'] = tags
            response.session['title'] = title
            response.session['difficulty'] = difficulty
            response.session['type'] = type_
            response.session['description'] = description
            return render(response, 'instructor/quiz.html',
                          {'count': range(1, count+1), 'title': title})

        elif response.POST.get('submit'):
            user = response.user.username

            question_ls = []
            count = int(response.session['count'])
            runtime = int(response.session['time'])
            tags = response.session['tags']
            title = response.session['title']
            difficulty = response.session['difficulty']
            type_ = response.session['type']
            description = response.session['description']

            total_marks = 0
            for i in range(1, count+1):
                total_marks += int(response.POST[f'mark-{i}'])
                q = {'question': response.POST[f'ques-{i}'],
                     'options': [response.POST[f'option{j+1}-{i}'] for j in range(4)],
                     'correct': response.POST[f'ans-{i}'],
                     'mark': response.POST[f'mark-{i}']}
                question_ls.append(q)

            new_quiz = QuizPost.objects.create(user=user, number=count, time_allot=runtime,
                                               tags=tags, title=title, total_marks=total_marks,
                                               difficulty=difficulty, attempt_count=0,
                                               live=True if type_ == 'live' else False,
                                               description=description)
            new_quiz.save()

            if type_ == 'live':
                start_time = datetime.strptime(response.session['start'].replace("T", " "), "%Y-%m-%d %H:%M")
                end_time = datetime.strptime(response.session['end'].replace("T", " "), "%Y-%m-%d %H:%M")
                live_model = LiveTime.objects.create(id=new_quiz.id,
                                                     start_time=start_time,
                                                     close_time=end_time)
                live_model.save()

            fn = str(new_quiz.id) + '.txt'
            with open(f'quiz-data/{fn}', 'w') as file:
                json.dump(question_ls, file)

            return redirect('/instructor/quiz-list')

    return render(response, 'instructor/quiz-intro.html')


@user_passes_test(instructor_check, login_url='/instructor/signin')
def quiz_list(response):

    user = response.user.username
    quiz_ls = QuizPost.objects.filter(user=user).all()

    ls = []
    for quiz in quiz_ls:
        if LiveTime.objects.filter(id=quiz.id).exists():
            ls.append(LiveTime.objects.get(id=quiz.id))
        else:
            ls.append('')

    return render(response, 'instructor/quiz-list.html', {'quiz_ls': zip(quiz_ls, ls)})


@user_passes_test(instructor_check, login_url='/instructor/signin')
def view_quiz(response):
    quiz_id = response.GET.get('quiz_id')
    quiz_model = QuizPost.objects.get(id=quiz_id)

    if response.method == 'POST':
        question_ls = []
        for i in range(1, quiz_model.number + 1):
            q = {'question': response.POST[f'ques-{i}'],
                 'options': [response.POST[f'option{j + 1}-{i}'] for j in range(4)],
                 'correct': response.POST[f'ans-{i}'],
                 'mark': response.POST[f'mark-{i}']}
            question_ls.append(q)

        with open(f'quiz-data/{quiz_id}.txt', 'w') as file:
            json.dump(question_ls, file)

        return redirect('/instructor/quiz-list')

    with open(f'quiz-data/{quiz_id}.txt', 'r') as file:
        data = json.load(file)

    return render(response, 'instructor/my-quiz.html', {'quiz_model': quiz_model, 'data': data})


@user_passes_test(instructor_check, login_url='/instructor/signin')
def my_account(response):
    user = response.user
    profile = InstructorProfile.objects.get(user=user)

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

            return redirect('my-profile')

        elif response.POST.get('save'):
            user_model = auth.authenticate(username=user.username, password=response.POST['current-pass'])
            if user_model is not None:
                if response.POST['new-pass'] == response.POST['confirm-pass']:
                    user.set_password(response.POST['new-pass'])
                    user.save()
                    user_model = auth.authenticate(username=user.username, password=response.POST['new-pass'])
                    auth.login(response, user_model)
                else:
                    messages.info(response, 'Passwords does not match!!')
            else:
                messages.info(response, 'Current password is wrong!!!')

            return redirect('my-profile')

    return render(response, 'instructor/profile.html', {'profile': profile, 'user': user})


@user_passes_test(instructor_check, login_url='/instructor/signin')
def quiz_result(response):
    quiz_id = response.GET.get('quiz_id')
    quiz_model = QuizPost.objects.get(id=quiz_id)

    lead_records = QuizRecord.objects.filter(id_quiz=quiz_id).order_by('-score')[:10]

    return render(response, 'instructor/quiz-result.html', {'records': lead_records,
                                                            'quiz': quiz_model})


@user_passes_test(instructor_check, login_url='/instructor/signin')
def all_record(response):
    quiz_id = response.GET.get('quiz_id')

    records = QuizRecord.objects.filter(id_quiz=quiz_id).order_by('-attempt_at')
    model = QuizPost.objects.get(id=quiz_id)

    return render(response, 'instructor/all-record.html', {'records': records, 'model': model})


@user_passes_test(instructor_check, login_url='/instructor/signin')
def logout_i(response):
    logout(response)

    return redirect('/')


@user_passes_test(instructor_check, login_url='/instructor/signin')
def delete_quiz(response):
    quiz_id = response.GET.get('quiz_id')
    quiz_model = QuizPost.objects.filter(id=quiz_id)
    live_model = LiveTime.objects.filter(id=quiz_id)

    if quiz_model.exists():
        quiz_model.delete()
    if live_model.exists():
        live_model.delete()

    return redirect('/instructor/quiz-list')


@user_passes_test(instructor_check, login_url='/instructor/signin')
def change_time(response):
    quiz_id = response.GET.get('quiz_id')
    start = datetime.strptime(response.GET.get('start').replace("T", " "), "%Y-%m-%d %H:%M")
    close = datetime.strptime(response.GET.get('close').replace("T", " "), "%Y-%m-%d %H:%M")
    model = LiveTime.objects.get(id=quiz_id)

    model.start_time = start
    model.close_time = close
    model.save()

    return redirect('/instructor/quiz-list')


def contact(response):
    if response.method == 'POST':
        name = response.POST['name']
        email = response.POST['email']
        subject = response.POST['subject']
        message = response.POST['message']

        contact_record = ContactRecord.objects.create(name=name, email=email, subject=subject, message=message)
        contact_record.save()

        src = response.POST.get('src')
        if src == 'instructor':
            return redirect('/instructor')
        elif src == 'learner':
            return redirect('/learner')
        elif src == 'main':
            return redirect('/')


@user_passes_test(instructor_check, login_url='/instructor/signin')
def home(response):

    return render(response, 'instructor/index.html')


def main(response):

    return render(response, 'instructor/main.html')
