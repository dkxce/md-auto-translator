name: Auto Translate Docs

on:
  push:
    branches:
      - main
    paths:
      - '**/*.md'
      - '!**/*.en.md'
  workflow_dispatch:
    inputs:
      translate_paths:
        description: 'Paths of .md files to translate (space/newline separated)'
        required: false
        default: ''
      convert_paths:
        description: 'Paths of .md files to convert to DOCX (space/newline separated)'
        required: false
        default: ''
      translate_skip:
        description: 'Paths/globs to EXCLUDE from translation (space/newline separated)'
        required: false
        default: ''
      convert_skip:
        description: 'Paths/globs to EXCLUDE from DOCX conversion (space/newline separated)'
        required: false
        default: ''

permissions:
  contents: write # Критично: дает права на запись файлов обратно в этот репо

jobs:
  run-translation:
    runs-on: ubuntu-latest
    steps:
      # 1. Скачиваем файлы текущего репозитория
      - name: Checkout code
        uses: actions/checkout@v4

      # 2. Вызываем ваш центральный экшен перевода
      # Значения можно задать paths-стилем (как в `paths:` слева):
      #   translate_paths: |
      #     docs/ru/intro.md
      #     docs/ru/guide.md
      #   translate_skip: |
      #     docs/ru/draft-*.md
      #     docs/ru/obsolete/
      # Ниже — передача из workflow_dispatch: ${{ inputs.* }}
      - name: Run Translator Action
        uses: dkxce/md-auto-translator@main
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          # Пример многострочных значений (paths-стиль). Для workflow_dispatch
          # используются инпуты: ${{ inputs.translate_paths }} и т.п.
          translate_paths: ${{ inputs.translate_paths }}
          convert_paths: ${{ inputs.convert_paths }}
          translate_skip: ${{ inputs.translate_skip }}
          convert_skip: ${{ inputs.convert_skip }}