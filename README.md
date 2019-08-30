# otus-platform-tests

# Запуск тестов в локальном окружении

## Prerequisites

Рекомендуется запускать на виртуальной машине для изоляции окружения.

Протестировано на `Ubuntu 18.04` установленной на виртуальную машину `VirtualBox 6.0.8`. Хост ОС: `macOs Mojave 10.14.6`

Параметры виртуальной машины: `CPU 4 cores, RAM 4096 MB`

*Важно:* При использовании менее 2х CPU cores таймаутов в тестах не хватает и происходят ложные падения!

## Как запустить тесты локально

 1. Клоним репозиторий с тестами `otus-platform-tests` : `git clone https://github.com/express42/otus-platform-tests.git`
 2. Переходим в ветку тестов для группы `2019-06`: `git checkout 2019-06`
 3. Скрипт можно запустить 2мя способами:
    3.1 Запуск с параметрами: `./local-run.sh {абсолютный-путь-к-локальной-папке-[gitname]_platform} {имя-папки-с-дз}`.
    Например: `./local-run.sh /Users/ivan.ivanov/Documents/src/ivan_platform kubernetes-networks`. Таким образом мы запустим
    локально тестирование Домашней Работы №3 по сетям.
    3.2 Запуск скрипта без параметров и указание путей в процессе выполенния: `./local-run.sh`.
    В результате скрипт попросит указать абсолютный путь к локальной папке {gitname}_platform: `Your local platform folder (something like /Users/sergii.sinienok/src/{gitname}_platform):`
    И название папки с ДЗ, которое хотим протестировать: `Homework dir you want me to check (kubernetes-intro or others):`
    Скрипт валидируе базовые ошибки пользовательского ввода. Читайте внимательно сообщения.

# Troubleshooting
 1. Ошибка `Error: a cluster with the name "kind" already exists` - выполните `kind delete cluster` для починки. Внимание!!! Это удалит дефолтный kind кластер с вашего локального окружения! Будьте бдительны!!!