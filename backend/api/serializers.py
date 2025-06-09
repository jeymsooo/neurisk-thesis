from rest_framework import serializers
from .models import UserProfile, EMGData, FeatureSet, RiskScore, TrainingAssignment, Session

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = '__all__'

class EMGDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = EMGData
        fields = '__all__'

class FeatureSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeatureSet
        fields = '__all__'

class RiskScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskScore
        fields = '__all__'

class TrainingAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingAssignment
        fields = '__all__'

class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = '__all__' 