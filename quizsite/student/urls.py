from django.urls import path
from . import views

urlpatterns = [
    path('take-quiz', views.take_quiz, name='take-quiz'),
    path('signin', views.signin, name='signin'),
    path('quiz-list', views.quiz_list, name='quiz-list'),
    path('my-profile', views.my_account, name='learner-profile'),
    path('countdown', views.countdown, name='countdown'),
    path('signup', views.signup, name='learner-signup'),
    path('all-quiz', views.all_quiz, name='all-quiz'),
    path('quiz-result', views.result_page, name='quiz-result'),
    path('quiz-review', views.review_page, name='quiz-review'),
    path('generate', views.generate, name='generate-l'),
    path('', views.home_page, name='l-home'),
    path('practice-quiz', views.practice_quiz, name='practice-quiz'),
    path('logout', views.logout_l, name='l-logout'),
    path('live-list', views.live_list, name='live-list'),
    path('instructor-list', views.instructor_list, name='instructor-list'),
    path('instructor-profile', views.instructor_profile, name='instructor-profile')
]
