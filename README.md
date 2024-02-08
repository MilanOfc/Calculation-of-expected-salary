# Расчет ожидаемой зарплаты
Скрипт собирает статистику с сайтов hh.ru и SuperJob.ru для вакансий программиста. Статистика собирается для
нижеперечисленных языков программирования, для города Москва, расчитывается средняя зарплата и выводится количество вакансий.
<details><summary>Список языков программирования</summary>

1. JavaScript
2. Java
3. Python
4. Ruby
5. PHP
6. C++
7. C#
8. Go
9. Shell

</details>

## Использование

Склонируйте проект себе на компьютер и переейдите в папку, в которой он расположен.

    git clone https://github.com/MilanOfc/Calculation-of-expected-salary.git
    cd ./Calculation-of-expected-salary

Установите необходимые зависимости.

    pip install -r requirements.txt

Для работы с API сайта SuperJobs необходимо получить [ключ](https://api.superjob.ru/), после сохраните его в файл .env

    echo SUPERJOB_KEY='%Ваш_Токен%' >> .env

Запустите скрипт.

    python3 main.py

## Результат работы скрипта
![image](https://github.com/MilanOfc/Calculation-of-expected-salary/assets/122183166/947530c8-ba45-4ef8-99c9-fb7af61d841e)


