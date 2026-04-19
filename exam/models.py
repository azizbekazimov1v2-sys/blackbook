from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


class CategoryChoices(models.TextChoices):
    ENGLISH = 'english', 'English'
    MATH = 'math', 'Math'
    ANALYSIS = 'analysis', 'Analysis'


class PremiumTypeChoices(models.TextChoices):
    ENGLISH = 'english', 'English Premium'
    MATH = 'math', 'Math Premium'
    ANALYSIS = 'analysis', 'Analysis Premium'


class UploadModeChoices(models.TextChoices):
    PDF_FIXED = 'pdf_fixed', 'PDF Fixed'
    LATEX = 'latex', 'LaTeX'
    PDF_BANK = 'pdf_bank', 'PDF Question Bank'


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='profile_images/', blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} profile"


class Test(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    category = models.CharField(
        max_length=20,
        choices=CategoryChoices.choices,
        default=CategoryChoices.ENGLISH
    )

    raw_content = models.TextField(blank=True, null=True)
    pdf_file = models.FileField(upload_to='pdfs/', blank=True, null=True)

    tex_file = models.FileField(upload_to='latex/', blank=True, null=True)
    latex_source = models.TextField(blank=True, null=True)

    upload_mode = models.CharField(
        max_length=20,
        choices=UploadModeChoices.choices,
        default=UploadModeChoices.PDF_FIXED
    )

    total_questions = models.PositiveIntegerField(default=0)
    pick_count = models.PositiveIntegerField(default=0)
    randomize_questions = models.BooleanField(default=False)

    time_limit_minutes = models.PositiveIntegerField(default=60)

    is_pdf_based = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False)
    is_premium = models.BooleanField(default=False)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.category})"


class Question(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField(blank=True)

    choice_a = models.CharField(max_length=500, blank=True, default='A')
    choice_b = models.CharField(max_length=500, blank=True, default='B')
    choice_c = models.CharField(max_length=500, blank=True, default='C')
    choice_d = models.CharField(max_length=500, blank=True, default='D')

    correct_choice = models.CharField(max_length=200, blank=True, null=True)
    order = models.PositiveIntegerField(default=1)

    pdf_page = models.PositiveIntegerField(default=1)
    source_number = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.test.title} - Q{self.order}"


class VideoCourse(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()

    category = models.CharField(
        max_length=20,
        choices=CategoryChoices.choices,
        default=CategoryChoices.ANALYSIS
    )

    thumbnail = models.URLField(blank=True, null=True)
    video_url = models.URLField(blank=True, null=True)
    video_file = models.FileField(upload_to='videos/', blank=True, null=True)

    is_premium = models.BooleanField(default=False)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class UserPremiumAccess(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    premium_type = models.CharField(max_length=20, choices=PremiumTypeChoices.choices)

    is_active = models.BooleanField(default=True)
    started_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ['user', 'premium_type']

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=30)
        super().save(*args, **kwargs)

    def is_valid(self):
        return self.is_active and self.expires_at and self.expires_at > timezone.now()


class TestAttempt(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='attempts')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    correct_count = models.PositiveIntegerField(default=0)
    wrong_count = models.PositiveIntegerField(default=0)
    unanswered_count = models.PositiveIntegerField(default=0)
    total_questions = models.PositiveIntegerField(default=0)

    score = models.PositiveIntegerField(default=200)
    percentage = models.DecimalField(max_digits=6, decimal_places=2, default=0)

    completed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.test.title} - {self.user} - {self.score}"


class TestAttemptAnswer(models.Model):
    attempt = models.ForeignKey(TestAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='attempt_answers')

    order = models.PositiveIntegerField(default=1)
    user_answer = models.CharField(max_length=200, blank=True, default='')
    correct_answer = models.CharField(max_length=200, blank=True, default='')
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"Attempt {self.attempt_id} - Q{self.order}"


# =========================
# CAREER MODE
# =========================

class CareerVideo(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    video_url = models.URLField(blank=True)
    video_file = models.FileField(upload_to='career_videos/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class CareerTest(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    pdf_file = models.FileField(upload_to='career_tests/', null=True, blank=True)
    total_questions = models.PositiveIntegerField(default=0)
    time_limit_minutes = models.PositiveIntegerField(default=15)
    pass_percentage = models.PositiveIntegerField(default=60)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class CareerQuestion(models.Model):
    test = models.ForeignKey(CareerTest, on_delete=models.CASCADE, related_name='questions')
    order = models.PositiveIntegerField(default=1)
    pdf_page = models.PositiveIntegerField(default=1)
    correct_answer = models.CharField(max_length=1)

    class Meta:
        ordering = ['order']
        unique_together = ['test', 'order']

    def __str__(self):
        return f"{self.test.title} - Q{self.order}"


class CareerTopic(models.Model):
    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(unique=True)
    icon = models.CharField(max_length=10, default='⚽')

    video = models.ForeignKey(
        CareerVideo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='topics'
    )
    test = models.ForeignKey(
        CareerTest,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='topics'
    )

    is_free = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.order}. {self.title}"


class CareerProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='career_progress')
    topic = models.ForeignKey(CareerTopic, on_delete=models.CASCADE, related_name='progress_items')

    video_done = models.BooleanField(default=False)
    test_passed = models.BooleanField(default=False)
    score_percent = models.DecimalField(max_digits=6, decimal_places=2, default=0)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'topic']

    def __str__(self):
        return f"{self.user.username} - {self.topic.title}"
# =========================
# COMMENTS (TEST + VIDEO)
# =========================

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    test = models.ForeignKey(
        Test,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='comments'
    )

    video = models.ForeignKey(
        VideoCourse,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='comments'
    )

    text = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        target = self.test.title if self.test else self.video.title if self.video else "Unknown"
        return f"{self.user.username} - {target}"