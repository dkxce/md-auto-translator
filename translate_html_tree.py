import os
import re
import sys
import glob
import fnmatch
import markdown
import uuid  # Добавлен для генерации уникальных UUID-якорей
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
    # ЗАЩИТА: Если в текст прорвался маркер хранилища картинок, не переводим его
    if "IMGVAULT" in clean_text:
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
    # ЗАМЕНА НА UUID: Полная изоляция картинок до парсинга и перевода
    # =========================================================================
    image_vault = {}

    def stash_image(match):
        full_tag = match.group(0)
        # Генерируем UUID без дефисов, создавая слитное буквенно-цифровое слово.
        # Парсеры таблиц воспринимают его как обычный текст и гарантированно не ломают.
        clean_uuid = str(uuid.uuid4()).replace("-", "")
        marker = f"IMGVAULT{clean_uuid}"
        image_vault[marker] = full_tag
        return marker

    # 1. Прячем HTML теги <img>
    md_content = re.sub(r'<img\s+[^>]*?>', stash_image, md_content, flags=re.IGNORECASE)

    # 2. Прячем стандартную разметку Маркдауна ![alt](src)
    md_content = re.sub(r'!\[[^\]]*?\]\([^)]+?\)', stash_image, md_content)

    # =========================================================================
    # ПЕРЕВОД СТРУКТУРЫ ДОКУМЕНТА (Картинки заменены на безопасные маркеры)
    # =========================================================================
    html_content = markdown.markdown(md_content, extensions=['tables', 'fenced_code'])
    soup = BeautifulSoup(html_content, "html.parser")

    # Шаг 1: Обработка заголовков
    for heading in soup.find_all(re.compile(r'^h[1-6]$')):
        orig_text = heading.get_text()
        orig_slug = orig_text.lower().replace(" ", "-")
        orig_slug = re.sub(r'[^a-z0-9-_]', '', orig_slug)
        
        # Переводим текст заголовка
        for string in heading.find_all(string=True):
            if isinstance(string, NavigableString) and string.strip():
                string.replace_with(translate_text(string))
        
        trans_text = heading.get_text()
        new_slug = make_slug(trans_text)
        anchor_mapping[f"#{orig_slug}"] = f"#{new_slug}"
        
        anchor_tag = soup.new_tag("a", attrs={"name": new_slug})
        heading.append(anchor_tag)

    # Шаг 2: КРЕДО ПЕРЕВОДА — Переводим строго конечные текстовые ноды (string=True),
    # исключая дублирование обработки и блоки кода/ссылок.
    for text_node in soup.find_all(string=True):
        if not text_node.strip():
            continue
            
        # Проверяем, не лежит ли текст внутри тегов кода или pre
        parent_names = [p.name for p in text_node.parents]
        if 'code' in parent_names or 'pre' in parent_names:
            continue
            
        # Заголовки мы уже обработали на Шаге 1, пропускаем их текстовые ноды здесь
        if any(re.match(r'^h[1-6]$', name) for name in parent_names):
            continue

        # Обновление локальных ссылок (если родитель — тег 'a')
        if text_node.parent.name == 'a' and text_node.parent.has_attr('href'):
            href = text_node.parent['href'].lower()
            if href.startswith('#') and href in anchor_mapping:
                text_node.parent['href'] = anchor_mapping[href]

        # Выполняем чистый перевод текстового узла
        translated_node_text = translate_text(text_node)
        text_node.replace_with(translated_node_text)

    # Шаг 3: Сборка базового Markdown текста из HTML структуры
    translated_html = str(soup)
    translated_md = mdify(
        translated_html, 
        heading_style="ATX", 
        strip=['script', 'style']
    )

    # =========================================================================
    # ОБРАТНАЯ ЗАМЕНА: Возвращаем оригинальные картинки по ключам UUID
    # =========================================================================
    # На всякий случай подчищаем возможные бэкслеши экранирования перед маркером
    translated_md = re.sub(r'\\(IMGVAULT[a-f0-9]+)', r'\1', translated_md)

    # Поштучно меняем текстовые UUID-маркеры на исходные теги картинок
    for marker, original_tag in image_vault.items():
        translated_md = translated_md.replace(marker, original_tag)

    # Очистка дублирующихся переносов строк
    translated_md = re.sub(r'\n{3,}', '\n\n', translated_md)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(translated_md)
    
    print(f"Успешно сохранен перевод: {output_path}")
    successful_count += 1
    
print(f"\nВсе обнаруженные файлы успешно обработаны! Всего переведено: {successful_count}")
