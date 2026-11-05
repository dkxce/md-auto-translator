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
