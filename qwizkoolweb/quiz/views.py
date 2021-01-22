from django.shortcuts import get_object_or_404
from django.db.models import Q
from rest_framework import generics, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from . import models
from . import serializers

from .models import Choice, Question, Quiz

import qwizkoolnlp
from qwizkoolnlp.quiz.Question import Question as QuestionNLP
from qwizkoolnlp.article.WebArticle import WebArticle
from qwizkoolnlp.article.WikipediaArticle import WikipediaArticle
from qwizkoolnlp.quiz.Quiz import Quiz as QuizNLP
from qwizkoolnlp.nlp.QkContext import QkContext
from qwizkoolnlp.utils.QkUtils import QkUtils
import time
import wikipedia
import sys

import threading


# Documentation:
# https://www.django-rest-framework.org/api-guide/viewsets/
# https://www.django-rest-framework.org/api-guide/filtering/#djangofilterbackend


# Create your views here.
class QuizViewSet(viewsets.ModelViewSet):
    queryset = models.Quiz.objects.all()
    serializer_class = serializers.QuizSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['id', 'title_text']
    
    # detail=False: operate on /quiz/  
    # detail=True: operate on /quiz/pk  E.g. /quiz/pk/create_questions
    @action(detail=False, methods=['post'])
    def create_quiz(self, request, pk=None):
        return Response({'status': 'parse completed'})

    @action(detail=True, methods=['get'])
    def create_questions(self, request, pk=None):
        quiz = self.get_object()
        quiz.status_text = 'PARSING'
        quiz.save()
        t = threading.Thread(target=create_quiz, args=[quiz.id])
        t.setDaemon(True)
        t.start()
        #create_quiz(quiz.title_text)
        return Response({'status': 'started parsing..'})        


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = models.Question.objects.all()
    serializer_class = serializers.QuestionSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['id', 'quiz']


class ChoiceViewSet(viewsets.ModelViewSet):
    queryset = models.Choice.objects.all()
    serializer_class = serializers.ChoiceSerializer       


 
def create_quiz(quiz_id):

    new_quiz = Quiz.objects.get(pk=quiz_id)

    qk_ctx = QkContext('small')
    wiki_article = WikipediaArticle(new_quiz.title_text, qk_ctx)

    try:
        wiki_article.open()
    #except wikipedia.exceptions.PageError as err:
    #    print("Page Error: {0}".format(err))
    #    return render(request, 'quiz/create_quiz_fail.html', context)
    #except wikipedia.exceptions.DisambiguationError as err:
    #    print("Disambiguation Error: {0}".format(err))
    #    return render(request, 'quiz/create_quiz_fail.html', context)
    except: # catch *all* exceptions
        e_str = format(sys.exc_info()[1])
        e_str_html = e_str.replace("\n", "<br />") 
        context = {
            'topic': new_quiz.title_text, 
            'information': e_str_html,
        }
        #return render(request, 'quiz/create_quiz_fail.html', context)

    wiki_article.parse()

    quiz_nlp = QuizNLP(wiki_article)
    print("The Quiz has " + str(len(quiz_nlp.questions)) + " questions.")

    #new_quiz = Quiz.objects.create(title_text=quiz_nlp.article.title, description_text=quiz_nlp.article.sentences[0])
    #new_quiz.save()

    for question in quiz_nlp.questions:
        new_question = Question.objects.create(quiz=new_quiz, question_text=question.question_line)
        new_question.save()
        new_quiz.question_count += 1
        new_quiz.save()
        
        for choice in question.choices:
            new_choice = Choice.objects.create(question=new_question, choice_text=choice, is_correct=(question.answer==choice))
            new_choice.save()

    first_question = list(new_quiz.question_set.all())[0] 
    context = {
        'topic': new_quiz.title_text, 
        'description' : quiz_nlp.article.sentences[0],
        'information' : "The Quiz has " + str(len(quiz_nlp.questions)) + " questions.",
        'question' : first_question               
        }

    new_quiz.status_text = 'READY'
    new_quiz.save()
    #return render(request, 'quiz/create_quiz_success.html', context)     