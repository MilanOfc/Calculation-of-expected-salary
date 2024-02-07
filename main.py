import requests
import pprint
from itertools import count
import time

BASE_HH_URL = 'https://api.hh.ru/vacancies/'
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


def fetch_records(url, params):
    for page in count():
        time.sleep(1)
        params['page'] = page
        page_response = requests.get(url, params=params)
        page_response.raise_for_status()
        page_payload = page_response.json()
        yield from page_payload['items']
        if page >= page_payload['pages'] or page >= 99:
            yield page_payload['found']


def predict_rub_salary(vacancy):
    salary = vacancy.get('salary')
    if salary:
        if salary['currency'] == 'RUR':
            if salary['from']:
                if salary['to']:
                    return (salary['from'] + salary['to']) / 2
                return salary['from'] * 1.2
            return salary['to'] * 0.8
    return None


prog_vacancy_id = 'программист'
vacancies_per_lang = {}
median_salary_per_lang = {}
for name in LANG_NAMES:
    salaries = []
    text = f'{prog_vacancy_id} {name}'
    params = {'text': text, 'area': 1, 'period': 30}
    for vacancy in fetch_records(BASE_HH_URL, params):
        if isinstance(vacancy, int):
            vacancies_per_lang[name] = vacancy
            break
        salaries.append(predict_rub_salary(vacancy))
    salaries = [salary for salary in salaries if salary]
    temp = {
        "vacancies_found": vacancies_per_lang[name],
        "vacancies_processed": len(salaries),
        "average_salary": int(sum(salaries) / len(salaries))
    }
    median_salary_per_lang[name] = temp

pprint.pprint(median_salary_per_lang)
