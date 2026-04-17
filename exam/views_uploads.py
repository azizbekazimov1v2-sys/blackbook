from io import BytesIO

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.files.base import ContentFile
from PyPDF2 import PdfReader, PdfMerger

from .models import Test, Question, VideoCourse
from .services import (
    parse_answer_key,
    compile_latex_to_pdf,
    create_questions_from_answer_list,
)


def _read_uploaded_file_bytes(uploaded_file):
    """
    request.FILES ichidan kelgan faylni bytes ko‘rinishida o‘qiydi.
    """
    uploaded_file.seek(0)
    data = uploaded_file.read()
    uploaded_file.seek(0)
    return data


def _read_field_file_bytes(field_file):
    """
    Django FieldFile (masalan test.pdf_file) ni bytes ko‘rinishida o‘qiydi.
    S3 / Railway bucket bilan ham ishlaydi.
    """
    field_file.open("rb")
    try:
        data = field_file.read()
    finally:
        field_file.close()
    return data


def _get_pdf_page_count_from_bytes(pdf_bytes):
    """
    PDF bytes dan sahifalar sonini qaytaradi.
    """
    reader = PdfReader(BytesIO(pdf_bytes))
    return len(reader.pages)


@login_required
def create_video(request):
    if not request.user.is_staff:
        return redirect('home')

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        video_url = request.POST.get('video_url', '').strip()
        video_file = request.FILES.get('video_file')
        category = request.POST.get('category', 'analysis')
        is_premium = request.POST.get('is_premium') == 'on'
        price = request.POST.get('price') or 0

        if not video_url and not video_file:
            messages.error(request, 'Video URL yoki video fayl yuklang.')
            return redirect('create_video')

        if video_file:
            allowed_extensions = ['.mp4', '.webm', '.mov', '.ogg']
            filename = video_file.name.lower()

            if not any(filename.endswith(ext) for ext in allowed_extensions):
                messages.error(request, 'Faqat .mp4, .webm, .mov, .ogg formatlar ruxsat etiladi.')
                return redirect('create_video')

        VideoCourse.objects.create(
            title=title,
            description=description,
            video_url=video_url if video_url else None,
            video_file=video_file if video_file else None,
            category=category,
            created_by=request.user,
            is_premium=is_premium,
            price=price
        )

        messages.success(request, 'Video qo‘shildi!')
        return redirect('admin_panel')

    return render(request, 'exam/create_video.html')


@login_required
def upload_sat_pdf(request):
    if not request.user.is_staff:
        return redirect('home')

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        category = request.POST.get('category', 'english')
        is_premium = request.POST.get('is_premium') == 'on'
        price = request.POST.get('price') or 0
        total_questions = int(request.POST.get('total_questions') or 0)
        time_limit_minutes = int(request.POST.get('time_limit_minutes') or 60)
        answer_key_text = request.POST.get('answer_key', '').strip()
        pdf_file = request.FILES.get('pdf_file')

        if not pdf_file:
            messages.error(request, 'PDF fayl tanlanmagan.')
            return redirect('upload_sat_pdf')

        if total_questions <= 0:
            messages.error(request, 'Savollar sonini to‘g‘ri kiriting.')
            return redirect('upload_sat_pdf')

        if time_limit_minutes <= 0:
            messages.error(request, 'Timer minutlari noto‘g‘ri.')
            return redirect('upload_sat_pdf')

        answers = parse_answer_key(answer_key_text)

        if len(answers) != total_questions:
            messages.error(
                request,
                f'Javoblar soni {total_questions} ta bo‘lishi kerak. Siz {len(answers)} ta kiritgansiz.'
            )
            return redirect('upload_sat_pdf')

        test = Test.objects.create(
            title=title,
            description=description,
            category=category,
            pdf_file=pdf_file,
            upload_mode='pdf_fixed',
            total_questions=total_questions,
            pick_count=total_questions,
            randomize_questions=False,
            time_limit_minutes=time_limit_minutes,
            is_pdf_based=True,
            created_by=request.user,
            is_premium=is_premium,
            price=price,
            is_published=False
        )

        pdf_bytes = _read_field_file_bytes(test.pdf_file)
        total_pages = _get_pdf_page_count_from_bytes(pdf_bytes)

        create_questions_from_answer_list(
            test=test,
            answers=answers,
            total_pages=total_pages,
            QuestionModel=Question,
            start_order=1,
            start_source_number=1,
            start_page=1,
        )

        test.is_published = True
        test.save()

        messages.success(request, f'{total_questions} ta savolli PDF test yaratildi.')
        return redirect('admin_panel')

    return render(request, 'exam/upload_sat_pdf.html')


@login_required
def upload_latex_test(request):
    if not request.user.is_staff:
        return redirect('home')

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        category = request.POST.get('category', 'english')
        is_premium = request.POST.get('is_premium') == 'on'
        price = request.POST.get('price') or 0
        time_limit_minutes = int(request.POST.get('time_limit_minutes') or 60)
        answer_key_text = request.POST.get('answer_key', '').strip()

        tex_file = request.FILES.get('tex_file')
        latex_source = request.POST.get('latex_source', '').strip()

        if not tex_file and not latex_source:
            messages.error(request, 'LaTeX fayl yoki LaTeX kod kiriting.')
            return redirect('upload_latex_test')

        if time_limit_minutes <= 0:
            messages.error(request, 'Timer minutlari noto‘g‘ri.')
            return redirect('upload_latex_test')

        answers = parse_answer_key(answer_key_text)
        if not answers:
            messages.error(request, 'Javoblar topilmadi.')
            return redirect('upload_latex_test')

        try:
            pdf_bytes = compile_latex_to_pdf(
                uploaded_tex_file=tex_file,
                latex_text=None if tex_file else latex_source
            )
        except Exception as e:
            messages.error(request, f'LaTeX compile xato: {str(e)[:1000]}')
            return redirect('upload_latex_test')

        test = Test.objects.create(
            title=title,
            description=description,
            category=category,
            latex_source=latex_source if latex_source else None,
            upload_mode='latex',
            total_questions=len(answers),
            pick_count=len(answers),
            randomize_questions=False,
            time_limit_minutes=time_limit_minutes,
            is_pdf_based=True,
            is_premium=is_premium,
            price=price,
            created_by=request.user,
            is_published=False,
        )

        test.pdf_file.save(f"{title}_compiled.pdf", ContentFile(pdf_bytes), save=False)

        if tex_file:
            test.tex_file = tex_file

        test.save()

        saved_pdf_bytes = _read_field_file_bytes(test.pdf_file)
        total_pages = _get_pdf_page_count_from_bytes(saved_pdf_bytes)

        create_questions_from_answer_list(
            test=test,
            answers=answers,
            total_pages=total_pages,
            QuestionModel=Question,
            start_order=1,
            start_source_number=1,
            start_page=1,
        )

        test.is_published = True
        test.save()

        messages.success(request, 'LaTeX test muvaffaqiyatli yaratildi.')
        return redirect('admin_panel')

    return render(request, 'exam/upload_latex_test.html')


@login_required
def upload_pdf_bank(request):
    if not request.user.is_staff:
        return redirect('home')

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        category = request.POST.get('category', 'english')
        price = request.POST.get('price') or 0
        total_questions = int(request.POST.get('total_questions') or 0)
        pick_count = int(request.POST.get('pick_count') or 44)
        time_limit_minutes = int(request.POST.get('time_limit_minutes') or 60)
        answer_key_text = request.POST.get('answer_key', '').strip()
        pdf_file = request.FILES.get('pdf_file')

        if not pdf_file:
            messages.error(request, 'PDF fayl tanlanmagan.')
            return redirect('upload_pdf_bank')

        if total_questions <= 0:
            messages.error(request, 'Savollar sonini to‘g‘ri kiriting.')
            return redirect('upload_pdf_bank')

        if time_limit_minutes <= 0:
            messages.error(request, 'Timer minutlari noto‘g‘ri.')
            return redirect('upload_pdf_bank')

        answers = parse_answer_key(answer_key_text)

        if len(answers) != total_questions:
            messages.error(
                request,
                f'Javoblar soni {total_questions} ta bo‘lishi kerak. Siz {len(answers)} ta kiritgansiz.'
            )
            return redirect('upload_pdf_bank')

        if pick_count <= 0 or pick_count > total_questions:
            messages.error(request, 'Random savollar soni noto‘g‘ri.')
            return redirect('upload_pdf_bank')

        test = Test.objects.create(
            title=title,
            description=description,
            category=category,
            pdf_file=pdf_file,
            upload_mode='pdf_bank',
            total_questions=total_questions,
            pick_count=pick_count,
            randomize_questions=True,
            time_limit_minutes=time_limit_minutes,
            is_pdf_based=True,
            created_by=request.user,
            is_premium=True,
            price=price,
            is_published=False
        )

        pdf_bytes = _read_field_file_bytes(test.pdf_file)
        total_pages = _get_pdf_page_count_from_bytes(pdf_bytes)

        create_questions_from_answer_list(
            test=test,
            answers=answers,
            total_pages=total_pages,
            QuestionModel=Question,
            start_order=1,
            start_source_number=1,
            start_page=1,
        )

        test.is_published = True
        test.save()

        messages.success(
            request,
            f'{total_questions} ta savoldan iborat bank yaratildi. Har attemptda {pick_count} ta random savol chiqadi.'
        )
        return redirect('admin_panel')

    return render(request, 'exam/upload_pdf_bank.html')


@login_required
def append_pdf_bank(request, test_id):
    if not request.user.is_staff:
        return redirect('home')

    test = get_object_or_404(Test, id=test_id, created_by=request.user, upload_mode='pdf_bank')

    if request.method == 'POST':
        pdf_file = request.FILES.get('pdf_file')
        answer_key_text = (request.POST.get('answer_key') or '').strip()
        new_total_questions = int(request.POST.get('total_questions') or 0)

        if not pdf_file:
            messages.error(request, 'Yangi PDF fayl tanlanmagan.')
            return redirect('append_pdf_bank', test_id=test.id)

        if new_total_questions <= 0:
            messages.error(request, 'Yangi qo‘shiladigan savollar sonini to‘g‘ri kiriting.')
            return redirect('append_pdf_bank', test_id=test.id)

        answers = parse_answer_key(answer_key_text)

        if len(answers) != new_total_questions:
            messages.error(
                request,
                f'Javoblar soni {new_total_questions} ta bo‘lishi kerak. Siz {len(answers)} ta kiritgansiz.'
            )
            return redirect('append_pdf_bank', test_id=test.id)

        old_pdf_bytes = _read_field_file_bytes(test.pdf_file)
        old_pages_count = _get_pdf_page_count_from_bytes(old_pdf_bytes)

        new_pdf_bytes = _read_uploaded_file_bytes(pdf_file)
        new_pages_count = _get_pdf_page_count_from_bytes(new_pdf_bytes)

        merger = PdfMerger()
        merger.append(BytesIO(old_pdf_bytes))
        merger.append(BytesIO(new_pdf_bytes))

        merged_buffer = BytesIO()
        merger.write(merged_buffer)
        merger.close()
        merged_buffer.seek(0)

        merged_filename = f"{test.title}_merged.pdf"
        test.pdf_file.save(merged_filename, ContentFile(merged_buffer.read()), save=False)

        existing_count = test.questions.count()

        create_questions_from_answer_list(
            test=test,
            answers=answers,
            total_pages=new_pages_count,
            QuestionModel=Question,
            start_order=existing_count + 1,
            start_source_number=existing_count + 1,
            start_page=old_pages_count + 1,
        )

        test.total_questions = test.questions.count()

        if test.pick_count > test.total_questions:
            test.pick_count = test.total_questions

        test.save()

        messages.success(
            request,
            f'Yangi PDF qo‘shildi. Bank endi {test.total_questions} ta savoldan iborat.'
        )
        return redirect('admin_panel')

    return render(request, 'exam/append_pdf_bank.html', {
        'test': test
    })