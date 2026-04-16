import os
import re
import random
import subprocess
import tempfile

from decimal import Decimal, InvalidOperation
from django.core.files.base import ContentFile
from PyPDF2 import PdfReader


def calculate_scaled_score(correct_count, total):
    if total == 0:
        return 200, 0

    percentage = round((correct_count / total) * 100, 2)
    raw_score = 200 + ((correct_count / total) * 600)
    score = int((raw_score + 5) // 10) * 10
    score = max(200, min(800, score))

    return score, percentage


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
                ans = ans.strip()
            else:
                ans = line.strip()

            if ans:
                answers.append(ans)
        return answers

    cleaned = ''.join(ch for ch in text if not ch.isspace())
    if cleaned and all(ch.upper() in ['A', 'B', 'C', 'D'] for ch in cleaned):
        return [ch.upper() for ch in cleaned]

    return [text]


def normalize_text_answer(value):
    value = str(value or '').strip().lower()
    value = value.replace('−', '-').replace('–', '-').replace('—', '-')
    value = re.sub(r'\s+', '', value)

    match = re.match(r'^[a-zA-Z]+\s*=\s*(.+)$', value)
    if match:
        value = match.group(1).strip()

    if value.startswith('='):
        value = value[1:].strip()

    return value


def parse_numeric_value(value):
    value = normalize_text_answer(value)
    if not value:
        return None

    value = value.replace(',', '')

    decimal_pattern = r'^[-+]?(?:\d+(?:\.\d+)?|\.\d+)$'
    fraction_pattern = r'^[-+]?\d+\/[-+]?\d+$'

    try:
        if re.fullmatch(decimal_pattern, value):
            return Decimal(value)

        if re.fullmatch(fraction_pattern, value):
            left, right = value.split('/')
            left = Decimal(left)
            right = Decimal(right)
            if right == 0:
                return None
            return left / right
    except (InvalidOperation, ZeroDivisionError):
        return None

    return None


def split_correct_answer_variants(correct_answer):
    raw = str(correct_answer or '').strip()
    if not raw:
        return []
    return [part.strip() for part in re.split(r'[|;]', raw) if part.strip()]


def smart_answers_match(user_answer, correct_answer):
    normalized_user = normalize_text_answer(user_answer)
    if not normalized_user:
        return False

    correct_variants = split_correct_answer_variants(correct_answer)
    if not correct_variants:
        correct_variants = [str(correct_answer or '').strip()]

    user_numeric = parse_numeric_value(normalized_user)

    for variant in correct_variants:
        normalized_correct = normalize_text_answer(variant)

        if normalized_user == normalized_correct:
            return True

        correct_numeric = parse_numeric_value(normalized_correct)

        if user_numeric is not None and correct_numeric is not None:
            if abs(user_numeric - correct_numeric) <= Decimal('0.000001'):
                return True

    return False


def compile_latex_to_pdf(uploaded_tex_file=None, latex_text=None):
    with tempfile.TemporaryDirectory() as tmpdir:
        tex_path = os.path.join(tmpdir, 'main.tex')

        if uploaded_tex_file:
            with open(tex_path, 'wb') as f:
                for chunk in uploaded_tex_file.chunks():
                    f.write(chunk)
        else:
            with open(tex_path, 'w', encoding='utf-8') as f:
                f.write(latex_text or '')

        cmd = [
            'pdflatex',
            '-interaction=nonstopmode',
            '-halt-on-error',
            '-no-shell-escape',
            'main.tex'
        ]

        result = subprocess.run(
            cmd,
            cwd=tmpdir,
            capture_output=True,
            text=True,
            timeout=30
        )

        pdf_path = os.path.join(tmpdir, 'main.pdf')
        if result.returncode != 0 or not os.path.exists(pdf_path):
            error_text = (result.stdout or '') + "\n" + (result.stderr or '')
            raise Exception(error_text[-3000:])

        with open(pdf_path, 'rb') as f:
            return f.read()


def create_questions_from_answer_list(
    test,
    answers,
    total_pages=1,
    QuestionModel=None,
    start_order=1,
    start_source_number=1,
    start_page=1,
):
    for local_index, ans in enumerate(answers, start=1):
        absolute_order = start_order + local_index - 1
        absolute_source_number = start_source_number + local_index - 1

        page_number = start_page + local_index - 1
        max_page = start_page + total_pages - 1 if total_pages > 0 else page_number
        if page_number > max_page:
            page_number = max_page

        QuestionModel.objects.create(
            test=test,
            text=f"Question {absolute_order}",
            choice_a='A',
            choice_b='B',
            choice_c='C',
            choice_d='D',
            correct_choice=str(ans).strip(),
            order=absolute_order,
            source_number=absolute_source_number,
            pdf_page=page_number,
        )


def get_selected_questions_for_attempt(request, test, QuestionModel=None):
    session_key = f"test_selection_{test.id}"

    if test.randomize_questions and test.pick_count > 0:
        selected_ids = request.session.get(session_key, [])

        all_ids = list(test.questions.values_list('id', flat=True))
        if not all_ids:
            return []

        cleaned_ids = []
        seen = set()
        valid_ids = set(all_ids)

        for qid in selected_ids:
            if qid in valid_ids and qid not in seen:
                cleaned_ids.append(qid)
                seen.add(qid)

        take_count = min(test.pick_count, len(all_ids))

        if len(cleaned_ids) < take_count:
            remaining_ids = [qid for qid in all_ids if qid not in seen]
            need_count = take_count - len(cleaned_ids)
            if need_count > 0:
                cleaned_ids.extend(random.sample(remaining_ids, need_count))

        selected_ids = cleaned_ids[:take_count]

        request.session[session_key] = selected_ids
        request.session.modified = True

        preserved_order = {qid: i for i, qid in enumerate(selected_ids)}
        questions = list(QuestionModel.objects.filter(id__in=selected_ids, test=test))
        questions.sort(key=lambda q: preserved_order[q.id])

        return questions

    return list(test.questions.all().order_by('order'))