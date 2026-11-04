import os
import glob
import subprocess
import fnmatch

def parse_env_list(env_name):
    """Читает вход из env строго по строкам, игнорируя пустые"""
    raw = os.environ.get(env_name, "").strip()
    if not raw:
        return []
    # Разделяем только по символу перевода строки
    paths = [p.strip().strip('"').strip("'") for p in raw.split("\n") if p.strip()]
    return paths

def convert_file(file_path, skip_patterns):
    """Проверяет паттерны исключений и конвертирует файл через Pandoc"""
    if not os.path.exists(file_path):
        print(f"Предупреждение: Файл не найден: {file_path}")
        return

    base_name = os.path.basename(file_path)
    # Проверка skip_patterns (поддержка glob-масок)
    if skip_patterns:
        if any(fnmatch.fnmatch(file_path, pat) or fnmatch.fnmatch(base_name, pat) for pat in skip_patterns):
            print(f"  Пропуск (convert_skip): {file_path}")
            return

    # Формируем имя .docx
    if file_path.endswith(".md"):
        out_path = file_path[:-3] + ".docx"
    else:
        out_path = file_path + ".docx"

    print(f"Конвертация: {file_path} -> {out_path}")
    try:
        subprocess.run(["pandoc", file_path, "-o", out_path], check=True)
    except Exception as e:
        print(f"Ошибка при конвертации {file_path}: {e}")

def main():
    convert_paths = parse_env_list("CONVERT_PATHS")
    convert_skip = parse_env_list("CONVERT_SKIP")

    if convert_paths:
        print("Конвертация по convert_paths")
        files_to_process = []
        
        for path_pattern in convert_paths:
            # Если в строке есть маски вроде * или **, раскрываем их динамически
            if "*" in path_pattern or "?" in path_pattern:
                # recursive=True позволяет обрабатывать ** (поиск во всех подпапках)
                matched_files = glob.glob(path_pattern, recursive=True)
                for f in matched_files:
                    if os.path.isfile(f) and f.endswith(".md"):
                        files_to_process.append(os.path.relpath(f, "."))
            else:
                # Если это обычный путь, добавляем как есть
                files_to_process.append(path_pattern)

        # Удаляем дубликаты с сохранением порядка
        seen = set()
        unique_files = [x for x in files_to_process if not (x in seen or seen.add(x))]

        # Запускаем конвертацию только для того, что было явно найдено или указано
        for f in unique_files:
            convert_file(f, convert_skip)
            
    else:
        print("Конвертация всех .md")
        all_md_files = []
        for root, dirs, files in os.walk("."):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for file in files:
                if file.endswith(".md"):
                    full_path = os.path.join(root, file)
                    clean_path = os.path.relpath(full_path, ".")
                    all_md_files.append(clean_path)

        ru_files = [f for f in all_md_files if not f.endswith(".en.md")]
        en_files = [f for f in all_md_files if f.endswith(".en.md")]

        for f in ru_files:
            convert_file(f, convert_skip)
        for f in en_files:
            convert_file(f, convert_skip)


if __name__ == "__main__":
    main()
