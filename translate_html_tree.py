import os
import re
import sys
import fnmatch
import markdown
from bs4 import BeautifulSoup, NavigableString
from markdownify import markdownify as mdify
from transliterate import slugify
import argostranslate.translate

def parse_env_list(env_name):
    """Читает вход из env: пути через пробел или перевод строки"""
    raw = os.environ.get(env_name, "").strip()
    return [p for p in raw.replace("\n", " ").split() if p.strip()]

def apply_skips(paths, skip_patterns):
    """Оставляет только те пути, которые не подпадают ни под один glob-паттерн из skip_patterns"""
    if not skip_patterns:
        return paths
    kept = []
    for p in paths:
        if any(fnmatch.fnmatch(p, pat) or fnmatch.fnmatch(os.path.basename(p), pat) for pat in skip_patterns):
            print(f"  Пропуск (translate_skip): {p}")
            continue
        kept.append(p)
    return kept

def translate_text(text):
    clean_text = text.strip()
    if not clean_text or clean_text.isdigit() or len(clean_text) < 2:
        return text
    try:
        return argostranslate.translate.translate(clean_text, "ru", "en")
    except Exception:
        return text

def make_slug(text):
    slug = slugify(text.lower())
    if not slug:
        slug = text.lower().replace(" ", "-")
    slug = re.sub(r'[^a-z0-9-_]', '', slug)
    return slug

def find_russian_markdown_files():
    """Автоматически находит все Markdown файлы для перевода, исключая английские и системные"""
    target_files = []
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for file in files:
            if file.endswith(".md"):
                if file.endswith(".en.md"): continue
                full_path = os.path.join(root, file)
                clean_path = os.path.relpath(full_path, ".")
                target_files.append(clean_path)
    return target_files

# Если вызваны явные пути через TRANSLATE_PATHS — используем их,
# иначе поиск файлов выполняется автоматически по всему репозиторию
skip_patterns = parse_env_list("TRANSLATE_SKIP")

if os.environ.get("TRANSLATE_PATHS", "").strip():
    files_to_translate = parse_env_list("TRANSLATE_PATHS")
else:
    files_to_translate = find_russian_markdown_files()

files_to_translate = apply_skips(files_to_translate, skip_patterns)

if not files_to_translate:
    print("Подходящие файлы для перевода не найдены.")
    sys.exit(0)

print(f"Найдено файлов для обработки: {len(files_to_translate)}")

for input_path in files_to_translate:
    if not os.path.exists(input_path):
        print(f"Предупреждение: Файл {input_path} не найден, пропускаем.")
        continue

    file_dir = os.path.dirname(input_path)
    file_name = os.path.basename(input_path)

    # Умное определение имени выходного файла перевода
    if "_ru.md" in file_name:
        out_name = file_name.replace("_ru.md", ".en.md")
    elif "-ru.md" in file_name:
        out_name = file_name.replace("-ru.md", ".en.md")
    elif ".ru.md" in file_name:
        out_name = file_name.replace(".ru.md", ".en.md")
    else:
        out_name = file_name.replace(".md", ".en.md")

    output_path = os.path.join(file_dir, out_name) if file_dir else out_name

    print(f"\n Обработка: {input_path} -> {output_path}")
    anchor_mapping = {}

    with open(input_path, "r", encoding="utf-8") as f:
        md_content = f.read()

    html_content = markdown.markdown(md_content, extensions=['tables', 'fenced_code'])
    soup = BeautifulSoup(html_content, "html.parser")

    # Шаг 1: Обработка заголовков и создание карты якорей
    for heading in soup.find_all(re.compile(r'^h[1-6]$')):
        orig_text = heading.get_text()
        orig_slug = orig_text.lower().replace(" ", "-")
        orig_slug = re.sub(r'[^a-z0-9-_]', '', orig_slug)
        
        for string in heading.find_all(string=True):
            if isinstance(string, NavigableString):
                string.replace_with(translate_text(string))
        
        trans_text = heading.get_text()
        new_slug = make_slug(trans_text)
        anchor_mapping[f"#{orig_slug}"] = f"#{new_slug}"
        
        anchor_tag = soup.new_tag("a", attrs={"name": new_slug})
        heading.append(anchor_tag)

    # Шаг 2: Перевод контента и обновление локальных ссылок
    for tag in soup.find_all(True):
        if tag.name in ['code', 'pre']:
            continue
        if tag.name == 'a' and tag.has_attr('href'):
            href = tag['href'].lower()
            if href.startswith('#') and href in anchor_mapping:
                tag['href'] = anchor_mapping[href]

        for child in tag.children:
            if isinstance(child, NavigableString) and child.strip():
                if tag.name not in ['code', 'pre'] and child.parent.name not in ['code', 'pre']:
                    child.replace_with(translate_text(child))

    # Шаг 3: Сборка и сохранение готового Markdown перевода
    translated_html = str(soup)
    translated_md = mdify(translated_html, heading_style="ATX", strip=['script', 'style'])
    translated_md = re.sub(r'\n{3,}', '\n\n', translated_md)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(translated_md)

    print(f"Успешно сохранен перевод: {output_path}")

print("\nВсе обнаруженные файлы успешно обработаны!")
