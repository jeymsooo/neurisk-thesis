from django.db import models

# Create your models here.

class UserProfile(models.Model):
    name = models.CharField(max_length=100)
    age = models.PositiveIntegerField()
    height = models.FloatField(help_text="Height in cm")
    weight = models.FloatField(help_text="Weight in kg")
    training_frequency = models.PositiveIntegerField(help_text="Sessions per week")
    previous_injury = models.CharField(max_length=50, choices=[
        ("none", "None"),
        ("calves", "Calves"),
        ("hamstrings", "Hamstrings"),
        ("quadriceps", "Quadriceps")
    ], default="none")
    muscle_group = models.CharField(max_length=50, choices=[
        ("calves", "Calves"),
        ("hamstrings", "Hamstrings"),
        ("quadriceps", "Quadriceps")
    ])
    contraction_type = models.CharField(max_length=50, choices=[
        ("isometric", "Isometric"),
        ("isotonic", "Isotonic")
    ])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.age})"

class Session(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="sessions")
    duration = models.PositiveIntegerField(help_text="Session duration in seconds")
    status = models.CharField(max_length=20, choices=[
        ("pending", "Pending"),
        ("collecting", "Collecting"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed")
    ], default="pending")
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    device_id = models.CharField(max_length=32, help_text="Device MAC address or unique ID", null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Session {self.id} for {self.user.name} ({self.status})"

class EMGData(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="emg_data")
    session = models.ForeignKey('Session', on_delete=models.CASCADE, related_name="emg_data", null=True, blank=True)
    raw_data = models.JSONField(help_text="Raw EMG signal data as a list of values")
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"EMGData for {self.user.name} at {self.timestamp}"

class FeatureSet(models.Model):
    emg_data = models.ForeignKey(EMGData, on_delete=models.CASCADE, related_name="feature_sets")
    features = models.JSONField(help_text="Extracted features from EMG data")
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"FeatureSet for {self.emg_data.user.name} at {self.timestamp}"

class RiskScore(models.Model):
    feature_set = models.ForeignKey(FeatureSet, on_delete=models.CASCADE, related_name="risk_scores")
    score = models.FloatField(help_text="Predicted risk score (numeric)")
    level = models.CharField(max_length=20, choices=[
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High")
    ])
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"RiskScore {self.level} ({self.score}) for {self.feature_set.emg_data.user.name}"

class TrainingAssignment(models.Model):
    risk_score = models.ForeignKey(RiskScore, on_delete=models.CASCADE, related_name="training_assignments")
    assignment = models.TextField(help_text="Assigned training based on risk score")
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"TrainingAssignment for {self.risk_score.feature_set.emg_data.user.name} ({self.risk_score.level})"
