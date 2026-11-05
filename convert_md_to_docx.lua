function RawInline(el)
  if el.format == "html" and el.text:lower():match("^<img") then
    local src = el.text:match('src%s*=%s*["\']([^"\']+)["\']')
    local width = el.text:match('width%s*=%s*["\']([^"\']+)["\']')
    local height = el.text:match('height%s*=%s*["\']([^"\']+)["\']')
    
    if src then
      local attr = {}
      
      -- Конвертируем ширину из px в дюймы (in) для совместимости со старыми Pandoc
      if width then 
        local num_width = tonumber(width:match("%d+"))
        if num_width then
          -- 96 пикселей в одном дюйме по стандарту Pandoc / Word
          local inches_width = num_width / 96
          attr['width'] = string.format("%.3fin", inches_width)
        end
      end
      
      -- Конвертируем высоту из px в дюймы (in)
      if height then 
        local num_height = tonumber(height:match("%d+"))
        if num_height then
          local inches_height = num_height / 96
          attr['height'] = string.format("%.3fin", inches_height)
        end
      end
      
      return pandoc.Image({}, src, "", attr)
    end
  end
end
