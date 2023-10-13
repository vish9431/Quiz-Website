from django.urls import path
from . import views

urlpatterns = [
    path('test', views.test, name='test'),
    path('make-quiz', views.make_quiz, name='make-quiz'),
    path('signin', views.signin, name='signin-i'),
    path('quiz-list', views.quiz_list, name='quiz-list'),
    path('my-quiz', views.view_quiz, name='my-quiz'),
    path('my-profile', views.my_account, name='my-profile'),
    path('signup', views.signup, name='signup-i'),
    path('logout', views.logout_i, name='i-logout'),
    path('quiz-result', views.quiz_result, name='quiz-result-i'),
    path('all-record', views.all_record, name='all-record'),
    path('delete-quiz', views.delete_quiz, name='delete-quiz'),
    path('change-time', views.change_time, name='change-time'),
    path('contact', views.contact, name='contact'),
    path('', views.home, name='i-home'),
]
