import os
import re
import sys
import glob
import fnmatch
import markdown
from bs4 import BeautifulSoup, NavigableString
from markdownify import markdownify as mdify
from transliterate import slugify
import argostranslate.translate

def parse_env_list(env_name):
    """Читает вход из env строго по строкам, игнорируя пустые"""
    raw = os.environ.get(env_name, "").strip()
    if not raw:
        return []
    # Разделяем только по символу перевода строки
    paths = [p.strip().strip('"').strip("'") for p in raw.split("\n") if p.strip()]
    return paths

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

def resolve_glob_paths(raw_paths):
    """Принимает список путей, раскрывает glob-маски (*, **) и возвращает уникальные пути к .md файлам"""
    resolved = []
    for path_pattern in raw_paths:
        if "*" in path_pattern or "?" in path_pattern:
            matched_files = glob.glob(path_pattern, recursive=True)
            for f in matched_files:
                if os.path.isfile(f) and f.endswith(".md"):
                    resolved.append(os.path.relpath(f, "."))
        else:
            resolved.append(path_pattern)
    
    seen = set()
    return [x for x in resolved if not (x in seen or seen.add(x))]

# Основная логика получения путей
skip_patterns = parse_env_list("TRANSLATE_SKIP")

if os.environ.get("TRANSLATE_PATHS", "").strip():
    raw_translate_paths = parse_env_list("TRANSLATE_PATHS")
    files_to_translate = resolve_glob_paths(raw_translate_paths)
else:
    files_to_translate = find_russian_markdown_files()

files_to_translate = apply_skips(files_to_translate, skip_patterns)

if not files_to_translate:
    print("Подходящие файлы для перевода не найдены.")
    sys.exit(0)

print(f"Найдено файлов для обработки: {len(files_to_translate)}")

successful_count = 0

for input_path in files_to_translate:
    if not os.path.exists(input_path):
        print(f"Предупреждение: Файл {input_path} не найден, пропускаем.")
        continue

    file_dir = os.path.dirname(input_path)
    file_name = os.path.basename(input_path)

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

    # =========================================================================
    # ШАГ 1 АЛГОРИТМА: Собираем оригинальные картинки из исходного текста (До перевода)
    # =========================================================================
    original_images = [] # Список кортежей: (чистый_путь, оригинальный_тег)
    
    # 1. Ищем HTML-теги <img ... /> (ленивый поиск `.*?` до закрывающего `>`)
    html_img_matches = re.findall(r'(<img\s+[^>]*?src=["\']([^"\']+)["\'][^>]*?>)', md_content)
    for full_tag, src in html_img_matches:
        original_images.append((src.strip(), full_tag.strip()))
        
    # 2. Ищем синтаксис маркдауна ![alt](src) (ленивый поиск `.*?` внутри скобок)
    md_img_matches = re.findall(r'(!\[[^\]]*?\]\(([^)]+?)\))', md_content)
    for full_tag, src in md_img_matches:
        # Отсекаем возможный title в кавычках внутри скобок, берем только путь
        clean_src = src.strip().split()[0] if src.strip() else ""
        original_images.append((clean_src, full_tag.strip()))

    # Парсинг и перевод через BeautifulSoup
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

    # Шаг 2: Перевод контента, атрибутов alt у картинок и обновление локальных ссылок
    for tag in soup.find_all(True):
        if tag.name in ['code', 'pre']:
            continue
            
        if tag.name == 'img' and tag.has_attr('alt'):
            tag['alt'] = translate_text(tag['alt'])
            
        if tag.name == 'a' and tag.has_attr('href'):
            href = tag['href'].lower()
            if href.startswith('#') and href in anchor_mapping:
                tag['href'] = anchor_mapping[href]

        for child in tag.children:
            if isinstance(child, NavigableString) and child.strip():
                if tag.name not in ['code', 'pre'] and child.parent.name not in ['code', 'pre']:
                    child.replace_with(translate_text(child))

    # Шаг 3: Сборка базового Markdown
    translated_html = str(soup)
    translated_md = mdify(
        translated_html, 
        heading_style="ATX", 
        strip=['script', 'style']
    )
    
    # Стандартизируем все маркдаун-картинки от markdownify в формат <img /> перед подсчетом
    markdown_img_regex = r'!\[(.*?)\]\((.*?)\)'
    def replace_with_html_img(match):
        alt_text = match.group(1)
        # Безопасно вытаскиваем только путь к картинке
        src_part = match.group(2).strip().split()[0] if match.group(2).strip() else ""
        return f'<img src="{src_part}" alt="{alt_text}" />'
    
    translated_md = re.sub(markdown_img_regex, replace_with_html_img, translated_md)

    # =========================================================================
    # ШАГ 2 АЛГОРИТМА: Собираем картинки из уже переведенного текста (После перевода)
    # =========================================================================
    translated_images = []
    translated_img_matches = re.findall(r'(<img\s+[^>]*?src=["\']([^"\']+)["\'][^>]*?>)', translated_md)
    for full_tag, src in translated_img_matches:
        translated_images.append((src.strip(), full_tag.strip()))

    # =========================================================================
    # ШАГ 3 АЛГОРИТМА: Сравнение числа файлов и замена на оригинал
    # =========================================================================
    if len(original_images) == len(translated_images):
        # Если количество совпало, последовательно заменяем теги на оригинальные
        for i in range(len(translated_images)):
            trans_src, trans_full_tag = translated_images[i]
            orig_src, orig_full_tag = original_images[i]
            
            # Проверка безопасности: пути к файлам картинок должны совпадать
            if trans_src == orig_src:
                # Третий аргумент `1` гарантирует замену только ОДНОГО (текущего) вхождения
                translated_md = translated_md.replace(trans_full_tag, orig_full_tag, 1)
    else:
        print(f"  Предупреждение: Дисбаланс картинок ({len(original_images)} в исходном vs {len(translated_images)} в переведенном). Размеры не восстановлены.")

    # Очистка дублирующихся переносов строк
    translated_md = re.sub(r'\n{3,}', '\n\n', translated_md)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(translated_md)

    print(f"Успешно сохранен перевод: {output_path}")
    successful_count += 1



print(f"\nВсе обнаруженные файлы успешно обработаны! Всего переведено: {successful_count}")
