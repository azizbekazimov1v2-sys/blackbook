from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import FileResponse, Http404

from .models import CareerTopic, CareerProgress, UserPremiumAccess


def user_has_premium(user):
    if user.is_staff or user.is_superuser:
        return True

    accesses = UserPremiumAccess.objects.filter(user=user, is_active=True)
    for access in accesses:
        try:
            if access.is_valid():
                return True
        except Exception:
            continue
    return False


def build_career_items(user):
    topics = CareerTopic.objects.filter(is_active=True).select_related('video', 'test').order_by('order')
    premium_enabled = user_has_premium(user)

    items = []
    previous_free_completed = True

    for topic in topics:
        progress, _ = CareerProgress.objects.get_or_create(user=user, topic=topic)
        completed = progress.video_done and progress.test_passed

        if topic.is_free:
            if topic.order == 1:
                unlocked = True
            else:
                unlocked = previous_free_completed
        else:
            unlocked = premium_enabled

        if topic.is_free:
            previous_free_completed = completed

        items.append({
            'topic': topic,
            'progress': progress,
            'completed': completed,
            'unlocked': unlocked,
            'locked': not unlocked,
            'has_video': topic.video is not None,
            'has_test': topic.test is not None,
        })

    total_topics = len(items)
    completed_topics = len([x for x in items if x['completed']])
    free_topics = len([x for x in items if x['topic'].is_free])
    progress_percent = round((completed_topics / total_topics) * 100) if total_topics > 0 else 0

    return {
        'items': items,
        'total_topics': total_topics,
        'completed_topics': completed_topics,
        'free_topics': free_topics,
        'progress_percent': progress_percent,
        'has_premium': premium_enabled,
    }


@login_required
def career_mode_view(request):
    context = build_career_items(request.user)
    return render(request, 'exam/career_mode.html', context)


@login_required
def secure_video_stream(request, topic_id):
    topic = get_object_or_404(CareerTopic, id=topic_id, is_active=True)

    state = build_career_items(request.user)
    item = next((x for x in state['items'] if x['topic'].id == topic.id), None)

    if not item or item['locked']:
        raise Http404("Bu video uchun ruxsat yo‘q.")

    if not topic.video or not topic.video.video_file:
        raise Http404("Video topilmadi.")

    try:
        topic.video.video_file.open("rb")
        response = FileResponse(topic.video.video_file, content_type="video/mp4")
        response["Content-Disposition"] = "inline"
        response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response["Pragma"] = "no-cache"
        response["Expires"] = "0"
        response["X-Content-Type-Options"] = "nosniff"
        return response
    except Exception:
        raise Http404("Video ochilmadi.")


@login_required
def career_watch_video(request, topic_id):
    topic = get_object_or_404(CareerTopic, id=topic_id, is_active=True)
    state = build_career_items(request.user)
    item = next((x for x in state['items'] if x['topic'].id == topic.id), None)

    if not item or item['locked']:
        messages.error(request, "Bu topic hozircha locked.")
        return redirect('career_mode')

    if not topic.video:
        messages.error(request, "Bu topic uchun video biriktirilmagan.")
        return redirect('career_mode')

    progress, _ = CareerProgress.objects.get_or_create(user=request.user, topic=topic)
    progress.video_done = True
    progress.save()

    if topic.video.video_url:
        return render(request, 'exam/career_watch_video.html', {
            'topic': topic,
            'external_video_url': topic.video.video_url,
            'is_external': True,
        })

    if topic.video.video_file:
        return render(request, 'exam/career_watch_video.html', {
            'topic': topic,
            'secure_video_url': f'/secure-video/{topic.id}/',
            'is_external': False,
        })

    messages.error(request, "Video manzili topilmadi.")
    return redirect('career_mode')


@login_required
def career_test_view(request, topic_id):
    topic = get_object_or_404(CareerTopic, id=topic_id, is_active=True)
    state = build_career_items(request.user)
    item = next((x for x in state['items'] if x['topic'].id == topic.id), None)

    if not item or item['locked']:
        messages.error(request, "Bu topic hozircha locked.")
        return redirect('career_mode')

    if not topic.test:
        messages.error(request, "Bu topic uchun test biriktirilmagan.")
        return redirect('career_mode')

    progress, _ = CareerProgress.objects.get_or_create(user=request.user, topic=topic)

    if not progress.video_done:
        messages.error(request, "Avval videoni ko‘rishingiz kerak.")
        return redirect('career_mode')

    questions = topic.test.questions.all().order_by('order')

    if questions.count() == 0:
        messages.error(request, "Bu testga hali savollar yaratilmagan.")
        return redirect('career_mode')

    if request.method == 'POST':
        total = questions.count()
        correct_count = 0

        for q in questions:
            selected = request.POST.get(f"question_{q.id}", "").strip().upper()
            if selected == (q.correct_answer or "").strip().upper():
                correct_count += 1

        percent = round((correct_count / total) * 100, 2) if total > 0 else 0

        progress.score_percent = percent
        progress.test_passed = percent >= topic.test.pass_percentage
        progress.save()

        return render(request, 'exam/career_result.html', {
            'topic': topic,
            'correct_count': correct_count,
            'total': total,
            'percent': percent,
            'passed': percent >= topic.test.pass_percentage,
            'pass_percentage': topic.test.pass_percentage,
        })

    pdf_url = topic.test.pdf_file.url if topic.test.pdf_file else ''

    return render(request, 'exam/career_test.html', {
        'topic': topic,
        'questions': questions,
        'time_limit_minutes': topic.test.time_limit_minutes,
        'pass_percentage': topic.test.pass_percentage,
        'pdf_url': pdf_url,
    })
@login_required
def add_video_comment(request, video_id):
    video = get_object_or_404(VideoCourse, id=video_id)

    if request.method == 'POST':
        text = request.POST.get('text', '').strip()
        if text:
            Comment.objects.create(user=request.user, video=video, text=text)

    return redirect('home')