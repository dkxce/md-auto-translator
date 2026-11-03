# .MD RU → EN Auto Translator

[RU](README.md) | [EN](README.en.md) | [SAMPLE](SAMPLE.md)         

Composite GitHub Action, который автоматически переводит Markdown-файлы на русском (`.md`) в английский (`.en.md`) и конвертирует Markdown в DOCX. Используется как переиспользуемый экшен: любой репозиторий может вызвать его через `uses:`.

## Возможности

- **Перевод RU → EN** через Argos Translate (без внешних API, работает offline в раннере).
- **Конвертация в DOCX** через Pandoc.
- **Выборочная обработка**: можно указать конкретные файлы для перевода и/или конвертации.
- **Фильтры исключения**: пропускаемые глоб-паттерны (`*`, `**`, `?`).
- Изменения коммитятся обратно в вызывающий репозиторий (`contents: write`).

## Как это работает

Экшен — это composite action, лежащий в этом репозитории. Внешний репозиторий подключает его в свой workflow через:

```yaml
uses: dkxce/md-auto-translator@main
```

и передаёт параметры через `with:`. Экшен сам:
1. ставит Pandoc и Python-пакеты,
2. устанавливает языковую модель Argos (RU→EN),
3. запускает перевод,
4. конвертирует в DOCX,
5. создаёт коммит `docs: auto-translate and convert to DOCX [skip ci]` и пушит.

## Входы (`inputs`)

| Вход | Обязателен | По умолчанию | Описание |
|------|-----------|--------------|----------|
| `github_token` | нет | `${{ github.token }}` | Токен записи. Подставляется автоматически; право записи даёт `permissions: contents: write` в вызывающем workflow. |
| `translate_paths` | нет | пусто | Пути `.md` файлов для перевода (через пробел/перенос строки). Пусто = автообнаружение всех `.md`. |
| `convert_paths` | нет | пусто | Пути `.md` файлов для конвертации в DOCX. Пусто = все `.md`. |
| `translate_skip` | нет | пусто | Глоб-паттерны для ИСКЛЮЧЕНИЯ из перевода. Пусто = переводить всё. |
| `convert_skip` | нет | пусто | Глоб-паттерны для ИСКЛЮЧЕНИЯ из конвертации в DOCX. Пусто = конвертировать всё. |

> **Пути и паттерны.** Несколько значений задаются через пробел или перевод строки (YAML-блок `: |`). В паттернах разрешены глобы: `*` (одна директория), `**` (рекурсивно), `?` (один символ).

## Требования к вызывающему репозиторию

Чтобы внешний репозиторий мог дёргать экшен, в его workflow должны быть:

- `permissions: contents: write` — иначе пуш коммита не пройдёт;
- шаг `actions/checkout@v4` со стандартным токеном (креденшл-персист включён по умолчанию);

## Примеры

### 1. Перевод и конвертация всех `.md`

Без указания файлов. Используется автообнаружение: переводятся и конвертируются все `.md` кроме `*.en.md` и `README.md`.

```yaml
name: Auto Translate Docs

on:
  push:
    branches: [main]
    paths:
      - '**/*.md'
      - '!**/*.en.md'

permissions:
  contents: write

jobs:
  translate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Translator
        uses: dkxce/md-auto-translator@main
        with:
```

### 2. Только перевод

Перевести `README.md` в `README.en.md`, **без** конвертации в DOCX. Конвертация отключается глобом `convert_skip: '**'`.

```yaml
name: Auto Translate Self

on:
  push:
    branches: [main]
    paths:
      - 'README.md'
  workflow_dispatch:

permissions:
  contents: write

jobs:
  translate-self:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Self Translation
        uses: dkxce/md-auto-translator@main
        with:
          translate_paths: README.md
          convert_skip: '**'
```

### 3. Только конвертация

Сконвертировать `.md` в DOCX, **без** перевода. Перевод отключается глобом `translate_skip: '**'`.

```yaml
name: Auto Translate Docs

on:
  push:
    branches: [main]
    paths:
      - '**/*.md'
      - '!**/*.en.md'

permissions:
  contents: write

jobs:
  translate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Translator
        uses: dkxce/md-auto-translator@main
        with:
          translate_skip: '**'
          convert_paths: |
            docs/ru/*.md
```

### 4. С указанием файлов к переводу (без конвертации)

Переводятся только перечисленные файлы, конвертация отключена (`convert_skip: '**'`).

```yaml
name: Auto Translate Docs

on:
  push:
    branches: [main]
    paths:
      - '**/*.md'
      - '!**/*.en.md'

permissions:
  contents: write

jobs:
  translate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Translator
        uses: dkxce/md-auto-translator@main
        with:
          translate_paths: |
            docs/ru/intro.md
            docs/ru/guide.md
          convert_skip: '**'
```

### 5. С указанием файлов к конвертации (без перевода)

Конвертируются только перечисленные файлы, перевод отключён (`translate_skip: '**'`).

```yaml
name: Auto Translate Docs

on:
  push:
    branches: [main]
    paths:
      - '**/*.md'
      - '!**/*.en.md'

permissions:
  contents: write

jobs:
  translate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Translator
        uses: dkxce/md-auto-translator@main
        with:
          translate_skip: '**'
          convert_paths: |
            docs/ru/intro.md
            docs/ru/guide.md
```

### 6. С указанием файлов к переводу (с конвертацией всех)

Переводятся только перечисленные файлы, конвертации не указана → конвертируются все `.md`.

```yaml
name: Auto Translate Docs

on:
  push:
    branches: [main]
    paths:
      - '**/*.md'
      - '!**/*.en.md'

permissions:
  contents: write

jobs:
  translate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Translator
        uses: dkxce/md-auto-translator@main
        with:
          translate_paths: |
            docs/ru/intro.md
            docs/ru/guide.md
```

### 7. С указанием файлов к конвертации (с переводом всех)

Конвертируются только перечисленные файлы, перевода не указан → переводятся все найденные `.md`.

```yaml
name: Auto Translate Docs

on:
  push:
    branches: [main]
    paths:
      - '**/*.md'
      - '!**/*.en.md'

permissions:
  contents: write

jobs:
  translate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Translator
        uses: dkxce/md-auto-translator@main
        with:
          convert_paths: |
            docs/ru/*.md
```

### 8. И перевод, и конвертация по конкретным файлам

Явно заданы оба списка: переводятся одни файлы, конвертируются другие (могут пересекаться, обрабатываются независимо).

```yaml
name: Auto Translate Docs

on:
  push:
    branches: [main]
    paths:
      - '**/*.md'
      - '!**/*.en.md'

permissions:
  contents: write

jobs:
  translate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Translator
        uses: dkxce/md-auto-translator@main
        with:
          translate_paths: |
            docs/ru/intro.md
            docs/ru/guide.md
            docs/ru/changelog.md
          convert_paths: |
            docs/ru/intro.md
            docs/ru/guide.md
```

### 9. С фильтрами пропуска (все кроме)

Обрабатываются **все** файлы (и перевод, и конвертация), **кроме** тех, что подпадают под глобы в `translate_skip` / `convert_skip`.

```yaml
name: Auto Translate Docs

on:
  push:
    branches: [main]
    paths:
      - '**/*.md'
      - '!**/*.en.md'

permissions:
  contents: write

jobs:
  translate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Translator
        uses: dkxce/md-auto-translator@main
        with:
          translate_skip: |
            docs/ru/draft-*.md
            docs/ru/obsolete/**
            notes/tmp*.md
          convert_skip: |
            docs/ru/draft-*.md
```

Здесь:
- `docs/ru/draft-*.md` — пропускаются все файлы с префиксом `draft-` в этой папке;
- `docs/ru/obsolete/**` — пропускается вся вложенная директория `obsolete`;
- `notes/tmp*.md` — файлы вида `tmp*.md` в папке `notes`.

## Полный рабочий пример (ручной запуск)

Пример с возможностью запуска вручную через `workflow_dispatch` (без объявления инпутов — параметры задаются в `with:`).

```yaml
name: Auto Translate Docs

on:
  push:
    branches: [main]
    paths:
      - '**/*.md'
      - '!**/*.en.md'
  workflow_dispatch:

permissions:
  contents: write

jobs:
  translate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Translator
        uses: dkxce/md-auto-translator@main
        with:
          translate_paths: |
            docs/ru/intro.md
            docs/ru/guide.md
          convert_skip: |
            docs/ru/draft-*.md
```

## Поведение по умолчанию

Таблица приоритетов:

| Сценарий | Перевод | Конвертация |
|----------|---------|-------------|
| `translate_paths` пусто | автообход всех `.md` | — |
| `translate_paths` задан | только перечисленные | — |
| `convert_paths` пусто | — | все `.md` (*.en.md включительно) |
| `convert_paths` задан | — | только перечисленные |
| `translate_skip` задан | исключает из перевода | — |
| `convert_skip` задан | — | исключает из конвертации |

## Структура репозитория

```
md-auto-translator/
├── action.yml              # composite action (главный вход)
├── translate_html_tree.py  # скрипт перевода RU→EN
└── sample.md               # пример workflow вызова
```

## Ограничения

- Argos-модель RU→EN скачивается при каждом запуске (шаг `Install Argos Model`). Для многих запусков стоит вынести установку модели в отдельный кеш.
- Перевод работает на уровне текстовых узлов: блоки кода и inline-код не переводятся (намеренно).
- `github_token` по умолчанию — `${{ github.token }}`; при использовании из внешнего репо токен берётся из вызывающего workflow.