from django.shortcuts import render


def clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))


def round_to_ten(value):
    return int(round(value / 10.0) * 10)


def estimate_section_score(correct_count, total_questions):
    correct_count = clamp(correct_count, 0, total_questions)
    raw_score = 200 + (correct_count / total_questions) * 600
    return clamp(round_to_ten(raw_score), 200, 800)


def score_calculator_view(request):
    result = None

    if request.method == 'POST':
        def get_int(name, default=0):
            try:
                return int(request.POST.get(name, default))
            except (TypeError, ValueError):
                return default

        rw_m1 = clamp(get_int('rw_m1'), 0, 27)
        rw_m2 = clamp(get_int('rw_m2'), 0, 27)
        math_m1 = clamp(get_int('math_m1'), 0, 22)
        math_m2 = clamp(get_int('math_m2'), 0, 22)

        rw_total = rw_m1 + rw_m2
        math_total = math_m1 + math_m2

        rw_score = estimate_section_score(rw_total, 54)
        math_score = estimate_section_score(math_total, 44)
        total_score = rw_score + math_score

        result = {
            'rw_m1': rw_m1,
            'rw_m2': rw_m2,
            'math_m1': math_m1,
            'math_m2': math_m2,
            'rw_total': rw_total,
            'math_total': math_total,
            'rw_score': rw_score,
            'math_score': math_score,
            'total_score': total_score,
        }

    return render(request, 'exam/score_calculator.html', {
        'result': result,
    })