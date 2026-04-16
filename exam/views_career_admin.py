from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from PyPDF2 import PdfReader

from .models import CareerVideo, CareerTest, CareerQuestion, CareerTopic


def parse_answer_key(answer_key_text):
    if not answer_key_text:
        return []

    text = answer_key_text.strip()
    if not text:
        return []

    lines = [line.strip() for line in text.splitlines() if line.strip()]

    if len(lines) > 1:
        answers = []
        for line in lines:
            if ':' in line:
                _, ans = line.split(':', 1)
                ans = ans.strip().upper()
            else:
                ans = line.strip().upper()

            if ans in ['A', 'B', 'C', 'D']:
                answers.append(ans)
        return answers

    cleaned = ''.join(ch for ch in text if not ch.isspace()).upper()
    if cleaned and all(ch in ['A', 'B', 'C', 'D'] for ch in cleaned):
        return [ch for ch in cleaned]

    return []


@login_required
def career_manager(request):
    if not request.user.is_staff:
        return redirect('home')

    topics = CareerTopic.objects.select_related('video', 'test').order_by('order')
    videos = CareerVideo.objects.all().order_by('-created_at')
    tests = CareerTest.objects.all().order_by('-created_at')

    editing_topic_id = request.GET.get('edit')
    editing_topic = None
    if editing_topic_id:
        editing_topic = CareerTopic.objects.filter(id=editing_topic_id).select_related('video', 'test').first()

    return render(request, 'exam/career_manager.html', {
        'topics': topics,
        'videos': videos,
        'tests': tests,
        'editing_topic': editing_topic,
    })


@login_required
def career_video_create(request):
    if not request.user.is_staff:
        return redirect('home')

    if request.method == 'POST':
        title = (request.POST.get('title') or '').strip()
        description = (request.POST.get('description') or '').strip()
        video_url = (request.POST.get('video_url') or '').strip()
        video_file = request.FILES.get('video_file')

        if not title:
            messages.error(request, "Video title kiritilishi kerak.")
            return redirect('career_manager')

        if not video_url and not video_file:
            messages.error(request, "Video URL yoki video file kerak.")
            return redirect('career_manager')

        if video_file:
            allowed_extensions = ['.mp4', '.webm', '.mov', '.ogg', '.m4v']
            filename = video_file.name.lower()

            if not any(filename.endswith(ext) for ext in allowed_extensions):
                messages.error(
                    request,
                    "Career video uchun faqat video formatlar ruxsat etiladi: .mp4, .webm, .mov, .ogg, .m4v"
                )
                return redirect('career_manager')

        CareerVideo.objects.create(
            title=title,
            description=description,
            video_url=video_url,
            video_file=video_file
        )

        messages.success(request, "Career video yaratildi.")
        return redirect('career_manager')

    return redirect('career_manager')


@login_required
def career_test_create(request):
    if not request.user.is_staff:
        return redirect('home')

    if request.method == 'POST':
        title = (request.POST.get('title') or '').strip()
        description = (request.POST.get('description') or '').strip()
        time_limit_minutes = int(request.POST.get('time_limit_minutes') or 15)
        pass_percentage = int(request.POST.get('pass_percentage') or 60)
        total_questions = int(request.POST.get('total_questions') or 0)
        answer_key_text = (request.POST.get('answer_key') or '').strip()
        pdf_file = request.FILES.get('pdf_file')

        if not title:
            messages.error(request, "Career test title kiritilishi kerak.")
            return redirect('career_manager')

        if not pdf_file:
            messages.error(request, "Career test uchun PDF file kerak.")
            return redirect('career_manager')

        if total_questions <= 0:
            messages.error(request, "Total questions noto‘g‘ri.")
            return redirect('career_manager')

        answers = parse_answer_key(answer_key_text)
        if len(answers) != total_questions:
            messages.error(
                request,
                f"Answer key soni {total_questions} ta bo‘lishi kerak. Hozir {len(answers)} ta."
            )
            return redirect('career_manager')

        test = CareerTest.objects.create(
            title=title,
            description=description,
            pdf_file=pdf_file,
            total_questions=total_questions,
            time_limit_minutes=time_limit_minutes,
            pass_percentage=pass_percentage,
        )

        pdf_reader = PdfReader(test.pdf_file.path)
        total_pages = len(pdf_reader.pages)

        for i, ans in enumerate(answers, start=1):
            page_number = i
            if total_pages > 0 and page_number > total_pages:
                page_number = total_pages

            CareerQuestion.objects.create(
                test=test,
                order=i,
                pdf_page=page_number,
                correct_answer=ans,
            )

        messages.success(request, "Career PDF test yaratildi.")
        return redirect('career_manager')

    return redirect('career_manager')


@login_required
def career_topic_create(request):
    if not request.user.is_staff:
        return redirect('home')

    if request.method == 'POST':
        title = (request.POST.get('title') or '').strip()
        subtitle = (request.POST.get('subtitle') or '').strip()
        description = (request.POST.get('description') or '').strip()
        order = int(request.POST.get('order') or 0)
        icon = (request.POST.get('icon') or '⚽').strip()
        video_id = request.POST.get('video_id')
        test_id = request.POST.get('test_id')
        is_free = request.POST.get('is_free') == 'on'
        is_active = request.POST.get('is_active') == 'on'

        if not title:
            messages.error(request, "Topic title kiritilishi kerak.")
            return redirect('career_manager')

        if order <= 0:
            messages.error(request, "Order 1 yoki undan katta bo‘lishi kerak.")
            return redirect('career_manager')

        if CareerTopic.objects.filter(order=order).exists():
            messages.error(request, "Bu order allaqachon ishlatilgan.")
            return redirect('career_manager')

        video = CareerVideo.objects.filter(id=video_id).first() if video_id else None
        test = CareerTest.objects.filter(id=test_id).first() if test_id else None

        CareerTopic.objects.create(
            title=title,
            subtitle=subtitle,
            description=description,
            order=order,
            icon=icon or '⚽',
            video=video,
            test=test,
            is_free=is_free,
            is_active=is_active,
        )

        messages.success(request, "Career topic yaratildi.")
        return redirect('career_manager')

    return redirect('career_manager')


@login_required
def career_topic_edit(request, topic_id):
    if not request.user.is_staff:
        return redirect('home')

    topic = get_object_or_404(CareerTopic, id=topic_id)

    if request.method == 'POST':
        title = (request.POST.get('title') or '').strip()
        subtitle = (request.POST.get('subtitle') or '').strip()
        description = (request.POST.get('description') or '').strip()
        order = int(request.POST.get('order') or 0)
        icon = (request.POST.get('icon') or '⚽').strip()
        video_id = request.POST.get('video_id')
        test_id = request.POST.get('test_id')
        is_free = request.POST.get('is_free') == 'on'
        is_active = request.POST.get('is_active') == 'on'

        if not title:
            messages.error(request, "Topic title kiritilishi kerak.")
            return redirect(f'/career-manager/?edit={topic.id}')

        if order <= 0:
            messages.error(request, "Order 1 yoki undan katta bo‘lishi kerak.")
            return redirect(f'/career-manager/?edit={topic.id}')

        if CareerTopic.objects.filter(order=order).exclude(id=topic.id).exists():
            messages.error(request, "Bu order allaqachon ishlatilgan.")
            return redirect(f'/career-manager/?edit={topic.id}')

        video = CareerVideo.objects.filter(id=video_id).first() if video_id else None
        test = CareerTest.objects.filter(id=test_id).first() if test_id else None

        topic.title = title
        topic.subtitle = subtitle
        topic.description = description
        topic.order = order
        topic.icon = icon or '⚽'
        topic.video = video
        topic.test = test
        topic.is_free = is_free
        topic.is_active = is_active
        topic.save()

        messages.success(request, "Career topic yangilandi.")
        return redirect('career_manager')

    return redirect('career_manager')


@login_required
def career_topic_delete(request, topic_id):
    if not request.user.is_staff:
        return redirect('home')

    topic = get_object_or_404(CareerTopic, id=topic_id)

    if request.method == 'POST':
        topic.delete()
        messages.success(request, "Career topic o‘chirildi.")

    return redirect('career_manager')