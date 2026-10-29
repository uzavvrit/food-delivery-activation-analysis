# Как опубликовать кейс на GitHub без терминала

Сначала разберись с `START_HERE.md`, затем публикуй. Старые приватные репозитории трогать не нужно.

## Через GitHub Desktop (Mac / Windows)

1. Скачай архив проекта и **распакуй его** в удобное место. Убедись, что видны файлы `README.md`, `START_HERE.md`, папки `sql`, `scripts`, `reports`, `docs`.
2. Установи [GitHub Desktop](https://desktop.github.com/) и войди в GitHub.
3. Открой **File → New Repository**. Название: `food-delivery-activation-analysis`. Выбери папку на компьютере и нажми **Create Repository**. Начальный README добавлять не нужно — он у тебя готов.
4. В GitHub Desktop выбери **Repository → Show in Finder** (Mac) или **Show in Explorer** (Windows). Откроется папка нового репозитория.
5. **Скопируй внутрь неё содержимое** распакованной папки проекта: `README.md`, `START_HERE.md`, `INTERVIEW_GUIDE.md`, `PUBLISH_ON_GITHUB.md`, `requirements.txt`, `Makefile`, `docs/`, `sql/`, `scripts/`, `tests/`, `reports/`, `data/`. Обязательно скопируй и скрытые `.github/`, `.gitignore` (на Mac скрытые файлы показываются сочетанием `Cmd + Shift + .`). **Не трогай папку `.git/`, которую создал GitHub Desktop.**
6. Вернись в GitHub Desktop. Слева появится список изменённых файлов. Внизу запиши Summary: `Add food delivery activation portfolio case`. Нажми **Commit to main**.
7. Нажми **Publish repository**. После того как **сама проверишь и поймёшь проект**, сними флажок **Keep this code private**, чтобы репозиторий стал публичным. Нажми **Publish Repository**.
8. Открой `https://github.com/uzavvrit/food-delivery-activation-analysis`. Увидишь README и графики. На своей главной странице GitHub нажми **Customize your pins** и закрепи новый репозиторий.

**Важно:** если не готова объяснить проект, можно сначала опубликовать **приватно** и сделать публичным после разбора.

Справка: [официальная инструкция GitHub Desktop](https://docs.github.com/en/desktop/overview/creating-your-first-repository-using-github-desktop).

## Что НЕ нужно загружать

Папку `data/raw/` с полным CSV. Она генерируется скриптом и уже внесена в `.gitignore`. Не загружай виртуальную среду `.venv/`, кэши Python или случайные личные файлы.

## Короткое описание репозитория для поля Description

`SQL + Python case study: first-order activation funnel, Android checkout diagnostics and A/B-test proposal (synthetic data).`
