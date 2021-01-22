from rest_framework import serializers

from . import models

class QuizSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Quiz
        fields = [
            'id',
            'title_text',
            'description_text',
            'pub_date',
            'status_text',
            'question_count'
        ]

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Question
        fields = [
            'id',            
            'quiz',
            'question_text',
            'attempted',
            'passed',
        ]

class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Choice
        fields = [
            'id',
            'question',
            'choice_text',
            'is_correct',
        ]    