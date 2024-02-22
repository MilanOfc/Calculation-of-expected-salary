import requests
import time
from terminaltables import AsciiTable
from environs import Env
from itertools import count

HH_URL = 'https://api.hh.ru/vacancies/'
SJ_URL = 'https://api.superjob.ru/2.0/vacancies/'
SJ_MOSCOW_ID = 4
SJ_INDUSTRY_ID = 48
HH_MOSCOW_ID = 1
HH_DAYS_PERIOD = 30
LANG_NAMES = [
    'JavaScript',
    'Java',
    'Python',
    'Ruby',
    'PHP',
    'C++',
    'C#',
    'Go',
    'Shell',
]
COLUMN_NAMES = [
    "Язык программирования",
    "Вакансий найдено",
    "Вакансий обработано",
    "Средняя зарплата",
]


def fetch_records_SJ(url, params, headers):
    for page in count():
        params['page'] = page
        page_response = requests.get(url, headers=headers, params=params)
        page_response.raise_for_status()
        page_payload = page_response.json()
        yield from page_payload['objects']
        if page_payload.get('more') == False:  # Cannot write "if not page_payload.get('more')", cause
            # "not None = True" but "None != False"
            yield page_payload['total']


def fetch_records_HH(url, params):
    for page in count():
        params['page'] = page
        page_response = requests.get(url, params=params)
        page_response.raise_for_status()
        page_payload = page_response.json()
        yield from page_payload['items']
        if page >= page_payload['pages'] or page >= 99:  # number of records per page - 20,
            # hh maximum allows you to download out 2000 records
            # that's why "page >= 99"
            yield page_payload['found']


def predict_salary(salary_from, salary_to):
    if salary_from:
        if salary_to:
            return (salary_from + salary_to) / 2
        return salary_from * 1.2
    return salary_to * 0.8


def predict_rub_salary_hh(vacancy):
    salary = vacancy.get('salary')
    if salary and salary['currency'] == 'RUR':
        return predict_salary(salary['from'], salary['to']) or None


def predict_rub_salary_sj(vacancy):
    if vacancy['currency'] == 'rub':
        return predict_salary(vacancy['payment_from'], vacancy['payment_to']) or None


def make_stat_per_lang_for_hh(params, salary_func):
    url = HH_URL
    vacancies_stats_per_lang = {}
    for lang_name in LANG_NAMES:
        salaries = []
        params['text'] = f"программист {lang_name}"
        for vacancy in fetch_records_HH(url, params):
            if isinstance(vacancy, int):
                amount_of_vacancies = vacancy
                break
            salaries.append(salary_func(vacancy))
        salaries = [salary for salary in salaries if salary]
        vacancies_stats_for_lang = {
            "vacancies_found": amount_of_vacancies,
            "vacancies_processed": len(salaries),
        }
        if not salaries:
            vacancies_stats_for_lang["average_salary"] = 0
        else:
            vacancies_stats_for_lang["average_salary"] = int(sum(salaries) / len(salaries))
        vacancies_stats_per_lang[lang_name] = vacancies_stats_for_lang
        time.sleep(30)  # without sleeptimer hh asks for CAPTCHA after 120 requests
    return vacancies_stats_per_lang


def make_stat_per_lang_for_sj(headers, params, salary_func):
    url = SJ_URL
    vacancies_stats_per_lang = {}
    for lang_name in LANG_NAMES:
        salaries = []
        params['keyword'] = lang_name
        for vacancy in fetch_records_SJ(url, params, headers):
            if isinstance(vacancy, int):
                amount_of_vacancies = vacancy
                break
            salaries.append(salary_func(vacancy))
        salaries = [salary for salary in salaries if salary]
        vacancies_stats_for_lang = {
            "vacancies_found": amount_of_vacancies,
            "vacancies_processed": len(salaries),
        }
        if not salaries:
            vacancies_stats_for_lang["average_salary"] = 0
        else:
            vacancies_stats_for_lang["average_salary"] = int(sum(salaries) / len(salaries))
        vacancies_stats_per_lang[lang_name] = vacancies_stats_for_lang
    return vacancies_stats_per_lang


def make_table(vacancies_statistics, platform_name):
    title = platform_name
    table_data = [COLUMN_NAMES]
    for lang_name, lang_statistics in vacancies_statistics.items():
        table_data.append([lang_name,
                           lang_statistics["vacancies_found"],
                           lang_statistics["vacancies_processed"],
                           lang_statistics["average_salary"],
                           ])
    return AsciiTable(table_data, title).table


if __name__ == '__main__':
    env = Env()
    env.read_env()
    sj_key = env('SUPERJOB_KEY')
    sj_headers = {'X-Api-App-Id': sj_key}
    sj_arguments = {
        'headers': sj_headers,
        'params': {'town': SJ_MOSCOW_ID, 'catalogues': SJ_INDUSTRY_ID},
        'salary_func': predict_rub_salary_sj,
    }
    hh_arguments = {
        'params': {'text': True, 'area': HH_MOSCOW_ID, 'period': HH_DAYS_PERIOD},
        'salary_func': predict_rub_salary_hh,
    }

    sj_stats = make_stat_per_lang_for_sj(**sj_arguments)
    hh_stats = make_stat_per_lang_for_hh(**hh_arguments)
    print(make_table(sj_stats, 'SuperJob Moscow'))
    print()
    print(make_table(hh_stats, 'HeadHunter Moscow'))
