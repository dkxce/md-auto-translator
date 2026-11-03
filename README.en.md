#MD Auto Translator

Composite GitHub Action, which automatically translates Markdown files into Russian`.md`in English ()`.en.md`) and converts Markdown to DOCX. Used as a reusable action: any repository can invoke it through`uses:`.

## Opportunities

* **Translated by EN**via Argos Translate (without external APIs, running offline in the runner).
* **Conversion to DOCX**Pandoc.
* **Selective processing**You can specify specific files for translation and/or conversion.
* **Exclusion filters**omitted globe patterns (`*`, `**`, `?`).
* Changes are Committed Back to the Calling Repository`contents: write`).

## How it works.

Action is a composite action that lies in this repository. The external repository connects it to its workflow through:

```
uses: dkxce/md-auto-translator@main
```

and transmits parameters through`with:`. Action itself:
1. puts Pandoc and Python packets,
2. establishes the Argos language model (RU→EN),
3. launches the translation,
4. convert to DOCX,
5. creates a commission.`docs: auto-translate and convert to DOCX [skip ci]`and fluff.

## Entrances`inputs`)

| Entrance | Mandatory. | By default. | Description |
| --- | --- | --- | --- |
| `github_token` | no | `${{ github.token }}` | Record token. Substitute automatically; the right to record`permissions: contents: write`in a challenging workflow. |
| `translate_paths` | no | empty | Ways.`.md`files for translation (through space/line transfer). Empty = Autodetection of All`.md`. |
| `convert_paths` | no | empty | Ways.`.md`Convert files to DOCX. Empty = everything`.md`. |
| `translate_skip` | no | empty | Globe patterns for EXCLUSION from translation. Empty means translating everything. |
| `convert_skip` | no | empty | Global patterns for EXCLUSION from DOCX conversion. Empty = convert everything. |

> **Paths and patterns.**Multiple values are given through space or line translation (YAML block).`: |`). The patterns allow globes:`*`(one directory),`**`(recursively)`?`(one symbol)

## Requirements for calling repositories

In order for an external repository to pull the action, its workflow should include:

* `permissions: contents: write`- or the commission's push won't pass;
* step`actions/checkout@v4`with a standard token (credenshale Persian is enabled by default);

## Examples.

### 1. No file details.

Transfer and convert**everything**automatically. Autodetection is used: all are located`.md`except`*.en.md` и `README.md`.

```
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

### 2. Indicating files for translation

Only the listed files are translated.`convert_paths`Not set to convert everything`.md`.

```
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

### 3. Indicating files for conversion

Only these files are converted to DOCX.`translate_paths`Not all of them have been translated.`.md`.

```
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

### 4. Translation and conversion of specific files

Both lists are clearly specified: some files are translated, others are converted (they can overlap, they are processed independently).

```
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

### 5. With pass filters (all except)

Processed.**everything**files (both translation and conversion),**except**those that fall under the globs in`translate_skip` / `convert_skip`.

```
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

Here:
-`docs/ru/draft-*.md`All files with prefixes are skipped.`draft-`in this folder;
-`docs/ru/obsolete/**`omitted the entire attached directory`obsolete`;
-`notes/tmp*.md`file`tmp*.md`file`notes`.

## Full working example (manual start)

An example of the ability to run manually through`workflow_dispatch`(without declaring inputs - parameters are set in`with:`).

```
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

## Default behaviour

Priority table:

| Script | Translation | Conversion |
| --- | --- | --- |
| `translate_paths`empty | roadside`.md` | — |
| `translate_paths`given | listed only | — |
| `convert_paths`empty | — | everything`.md`(\*.en.md inclusive) |
| `convert_paths`given | — | listed only |
| `translate_skip`given | exclude | — |
| `convert_skip`given | — | exclude |

## Structure of the repository

```
md-auto-translator/
├── action.yml              # composite action (главный вход)
├── translate_html_tree.py  # скрипт перевода RU→EN
└── sample.md               # пример workflow вызова
```

## Limitations

* Argos-model RU→EN downloads at each launch (step)`Install Argos Model`). For many launches, it is worth installing the model in a separate cache.
* Translation works at the level of text nodes: blocks of code and inline code are not translated (intentionally).
* `github_token`By default,`${{ github.token }}`When used from external repo, the token is taken from the calling workflow.