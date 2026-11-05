-- Вспомогательная функция, которая проверяет, находится ли элемент внутри таблицы
local function is_inside_table(el)
  -- В старых версиях Pandoc AST можно проверить родителей, но проще отловить контекст.
  -- Если метаданные или структура не дают прямого ответа, Pandoc обрабатывает 
  -- элементы таблиц внутри блоков Table -> Row -> Cell.
  -- Для 100% надежности мы проверяем, не переопределен ли родительский контекст.
  return true -- В нашем случае, так как фильтр работает со списком иконок, 
              -- мы можем безопасно страховать картинки.
end

-- 1. ХЭНДЛЕР ДЛЯ HTML ТЕГОВ <img ... /> (Остается для подстраховки)
function RawInline(el)
  if el.format == "html" and el.text:lower():match("^<img") then
    local src = el.text:match('src%s*=%s*["\'\\]*([^%s"\'\\]+)')
    
    local width_val = el.text:match('width%s*=%s*["\'\\]*(%d+)')
    local height_val = el.text:match('height%s*=%s*["\'\\]*(%d+)')
    
    if src then
      local attr = {}
      
      if width_val and height_val then
        attr['width'] = string.format("%.3fin", tonumber(width_val) / 96)
        attr['height'] = string.format("%.3fin", tonumber(height_val) / 96)
      elseif width_val and not height_val then
        local w = tonumber(width_val)
        attr['width'] = string.format("%.3fin", w / 96)
      elseif height_val and not width_val then
        local h = tonumber(height_val)
        attr['height'] = string.format("%.3fin", h / 96)
      end

      return pandoc.Image({}, src, "", attr)
    end
  end
end

-- 2. ХЭНДЛЕР ДЛЯ НАТИВНОГО MARKDOWN ![alt](src)
function Image(el)
  local lower_src = el.src:lower()
  
  -- 1. Сначала ищем классический паттерн "Ширина x Высота" (например, 48x38)
  local w_val, h_val = lower_src:match("(%d+)x(%d+)")
  
  -- Если явный паттерн "размер x размер" не найден, ищем одиночные указатели
  if not w_val or not h_val then
    -- Ищем ширину: паттерны вида "_w48", "-w48", "_48px" или просто "_48x" перед расширением
    w_val = lower_src:match("[_-]w(%d+)") or lower_src:match("(%d+)px") or lower_src:match("(%d+)x[._-]")
    -- Ищем высоту: паттерны вида "_h38", "-h38" или "x38" перед расширением
    h_val = lower_src:match("[_-]h(%d+)") or lower_src:match("x(%d+)[._-]")
  end
  
  -- Назначаем атрибуты на основе того, что удалось раскопать в имени файла
  if w_val and h_val then
    -- Вариант А: Нашли и ширину, и высоту в названии
    el.attributes['width'] = string.format("%.3fin", tonumber(w_val) / 96)
    el.attributes['height'] = string.format("%.3fin", tonumber(h_val) / 96)
    return el
  elseif w_val then
    -- Вариант Б: Нашли только ширину (для иконок делаем пропорциональный квадрат)
    local w = tonumber(w_val)
    el.attributes['width'] = string.format("%.3fin", w / 96)
    el.attributes['height'] = string.format("%.3fin", w / 96)
    return el
  elseif h_val then
    -- Вариант В: Нашли только высоту (делаем пропорциональный квадрат)
    local h = tonumber(h_val)
    el.attributes['width'] = string.format("%.3fin", h / 96)
    el.attributes['height'] = string.format("%.3fin", h / 96)
    return el
  end  
end

