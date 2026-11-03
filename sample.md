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