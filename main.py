import requests
import time
from terminaltables import AsciiTable
from environs import Env
from itertools import count

HH_URL = 'https://api.hh.ru/vacancies/'
SJ_URL = 'https://api.superjob.ru/2.0/vacancies/'
LANG_NAMES = [
    'JavaScript',
    'Java',
    'Python',
    'Ruby',
    'PHP',
    'C++',
    'C#',
    'Go',
    'Shell'
    ]
COLUMN_NAMES = [
    "Язык программирования",
    "Вакансий найдено",
    "Вакансий обработано",
    "Средняя зарплата"
    ]


def fetch_records(url, params, amount_kw, items_kw, headers=None):
    if headers is None:
        headers = {}
    for page in count():
        params['page'] = page
        page_response = requests.get(url, headers=headers, params=params)
        page_response.raise_for_status()
        page_payload = page_response.json()
        yield from page_payload[items_kw]
        if page_payload.get('pages'):
            if page >= page_payload['pages'] or page >= 99:  # number of records per page - 20,
                                                             # hh maximum allows you to dowload out 2000 records
                                                             # that's why "page >= 99"
                yield page_payload[amount_kw]
        if page_payload.get('more') == False:  # Cannot write "if not page_payload.get('more')", cause
            # "not None = True" but "None != False"
            yield page_payload[amount_kw]


def predict_salary(salary_from, salary_to):
    if salary_from:
        if salary_to:
            return (salary_from + salary_to) / 2
        return salary_from * 1.2
    return salary_to * 0.8


def predict_rub_salary_hh(vacancy):
    salary = vacancy.get('salary')
    if salary:
        if salary['currency'] == 'RUR':
            return predict_salary(salary['from'], salary['to']) or None


def predict_rub_salary_sj(vacancy):
    if vacancy['currency'] == 'rub':
        return predict_salary(vacancy['payment_from'], vacancy['payment_to']) or None


def make_stat_per_lang_for_hh_and_sj(url, headers, params, amount_kw, items_kw, sleep_timer, salary_func):
    vacancies_stats_per_lang = {}
    for lang_name in LANG_NAMES:
        salaries = []
        if params.get('text'):
            params['text'] = f"программист {lang_name}"
        else:
            params['keyword'] = lang_name
        for vacancy in fetch_records(url,
                                     params,
                                     headers=headers,
                                     amount_kw=amount_kw,
                                     items_kw=items_kw,
                                     ):
            if isinstance(vacancy, int):
                amount_of_vacancies = vacancy
                break
            salaries.append(salary_func(vacancy))
        salaries = [salary for salary in salaries if salary]
        temp = {
            "vacancies_found": amount_of_vacancies,
            "vacancies_processed": len(salaries),
        }
        if len(salaries) == 0:
            temp["average_salary"] = 0
        else:
            temp["average_salary"] = int(sum(salaries) / len(salaries))
        vacancies_stats_per_lang[lang_name] = temp
        time.sleep(sleep_timer)  # without sleeptimer hh asks for CAPTCHA after 120 requests
    return vacancies_stats_per_lang


def make_table(vacancies_information, platform_name):
    title = platform_name
    table_data = [COLUMN_NAMES]
    for key, value in vacancies_information.items():
        table_data.append([key, value["vacancies_found"], value["vacancies_processed"], value["average_salary"]])
    return AsciiTable(table_data, title).table


if __name__ == '__main__':
    env = Env()
    env.read_env()
    sj_key = env('SUPERJOB_KEY')
    sj_headers = {'X-Api-App-Id': sj_key}
    sj_arguments = {
        'url': SJ_URL,
        'headers': sj_headers,
        'params': {'town': 4, 'catalogues': 48},
        'amount_kw': 'total',
        'items_kw': 'objects',
        'sleep_timer': 0,
        'salary_func': predict_rub_salary_sj,
    }
    hh_arguments = {
        'url': HH_URL,
        'headers': None,
        'params': {'text': True, 'area': 1, 'period': 30},
        'amount_kw': 'found',
        'items_kw': 'items',
        'sleep_timer': 30,
        'salary_func': predict_rub_salary_hh,
    }

    hh_stats = make_stat_per_lang_for_hh_and_sj(**hh_arguments)
    sj_stats = make_stat_per_lang_for_hh_and_sj(**sj_arguments)
    print(make_table(sj_stats, 'SuperJob Moscow'))
    print()
    print(make_table(hh_stats, 'HeadHunter Moscow'))
