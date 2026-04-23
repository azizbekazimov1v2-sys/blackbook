from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from django.http import FileResponse, Http404
from .models import Comment

from .models import Test, Question, VideoCourse, UserPremiumAccess, TestAttempt, TestAttemptAnswer, Comment
from .services import (
    calculate_scaled_score,
    smart_answers_match,
    get_selected_questions_for_attempt,
)


def has_category_access(user, category):
    if not user.is_authenticated:
        return False

    if user.is_staff or user.is_superuser:
        return True

    access = UserPremiumAccess.objects.filter(
        user=user,
        premium_type=category,
        is_active=True
    ).first()

    return access.is_valid() if access else False


@login_required
def check_access(request, content_type, content_id):
    if content_type == 'test':
        content = get_object_or_404(Test, id=content_id)

        if has_category_access(request.user, content.category):
            return redirect('take_pdf_test', test_id=content.id)

    elif content_type == 'video':
        content = get_object_or_404(VideoCourse, id=content_id)

        if has_category_access(request.user, content.category):
            if content.video_url:
                return redirect(content.video_url)
            if content.video_file:
                return redirect(content.video_file.url)
            return redirect('home')
    else:
        return redirect('home')

    return render(request, 'exam/premium_block.html', {
        'content': content,
        'content_type': content_type,
        'telegram': 'Azizbek_Az1mov'
    })


@login_required
def pdf_proxy(request, test_id):
    test = get_object_or_404(Test, id=test_id, is_published=True)

    if test.is_premium and not has_category_access(request.user, test.category):
        raise Http404("PDF not available")

    if not test.pdf_file:
        raise Http404("PDF file not found")

    try:
        test.pdf_file.open("rb")
        response = FileResponse(
            test.pdf_file,
            content_type="application/pdf"
        )
        response["Content-Disposition"] = f'inline; filename="{test.title}.pdf"'
        return response
    except Exception:
        raise Http404("Unable to open PDF")


@login_required
def take_pdf_test(request, test_id):
    test = get_object_or_404(Test, id=test_id, is_published=True)

    if test.is_premium and not has_category_access(request.user, test.category):
        return redirect('check_access', content_type='test', content_id=test.id)

    questions = get_selected_questions_for_attempt(
        request=request,
        test=test,
        QuestionModel=Question,
    )

    return render(request, 'exam/take_pdf_test.html', {
        'test': test,
        'questions': questions,
        'desmos_api_key': getattr(settings, 'DESMOS_API_KEY', ''),
        'pdf_proxy_url': f"/pdf-proxy/{test.id}/",
        'comments': test.comments.all().order_by('-created_at'),
    })


@login_required
def submit_pdf_test(request, test_id):
    test = get_object_or_404(Test, id=test_id, is_published=True)

    if test.is_premium and not has_category_access(request.user, test.category):
        return redirect('check_access', content_type='test', content_id=test.id)

    questions = get_selected_questions_for_attempt(
        request=request,
        test=test,
        QuestionModel=Question,
    )

    if request.method == 'POST':
        correct_count = 0
        wrong_count = 0
        unanswered_count = 0
        total = len(questions)
        results = []

        for index, q in enumerate(questions, start=1):
            raw_user_answer = request.POST.get(f'q_{q.id}', '').strip()
            raw_correct_answer = (q.correct_choice or '').strip()

            if not raw_user_answer:
                is_correct = False
                unanswered_count += 1
            else:
                is_correct = smart_answers_match(raw_user_answer, raw_correct_answer)
                if is_correct:
                    correct_count += 1
                else:
                    wrong_count += 1

            results.append({
                'question': q,
                'order': index,
                'question_text': q.text,
                'user_answer': raw_user_answer if raw_user_answer else 'No Answer',
                'correct_answer': raw_correct_answer,
                'is_correct': is_correct,
                'pdf_page': q.pdf_page,
                'source_number': q.source_number,
            })

        score, percentage = calculate_scaled_score(correct_count, total)

        attempt = TestAttempt.objects.create(
            test=test,
            user=request.user,
            correct_count=correct_count,
            wrong_count=wrong_count,
            unanswered_count=unanswered_count,
            total_questions=total,
            score=score,
            percentage=percentage
        )

        for item in results:
            TestAttemptAnswer.objects.create(
                attempt=attempt,
                question=item['question'],
                order=item['order'],
                user_answer='' if item['user_answer'] == 'No Answer' else item['user_answer'],
                correct_answer=item['correct_answer'],
                is_correct=item['is_correct'],
            )

        session_key = f"test_selection_{test.id}"
        if session_key in request.session:
            del request.session[session_key]
            request.session.modified = True

        return render(request, 'exam/results_pdf.html', {
            'test': test,
            'correct_count': correct_count,
            'wrong_count': wrong_count,
            'unanswered_count': unanswered_count,
            'total': total,
            'score': score,
            'percentage': percentage,
            'results': results,
        })

    return redirect('take_pdf_test', test_id=test.id)
# =========================
# TEST COMMENTS
# =========================

@login_required
def add_test_comment(request, test_id):
    test = get_object_or_404(Test, id=test_id)

    if request.method == 'POST':
        text = request.POST.get('text', '').strip()
        if text:
            Comment.objects.create(user=request.user, test=test, text=text)

    return redirect('home')


@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    if comment.user == request.user or request.user.is_staff:
        comment.delete()

    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required
def share_test(request, test_id):
    test = get_object_or_404(Test, id=test_id)
    link = request.build_absolute_uri(f"/take-pdf-test/{test.id}/")
    return HttpResponse(link)