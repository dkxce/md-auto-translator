function RawInline(el)
  if el.format == "html" and el.text:lower():match("^<img") then
    local src = el.text:match('src%s*=%s*["\']([^"\']+)["\']')
    local width = el.text:match('width%s*=%s*["\']([^"\']+)["\']')
    local height = el.text:match('height%s*=%s*["\']([^"\']+)["\']')
    
    if src then
      local attr = {}
      
      if width then 
        local clean_width = width:gsub("px", ""):gsub("%s+", "")
        attr['width'] = clean_width .. "px" 
      end
      
      if height then 
        local clean_height = height:gsub("px", ""):gsub("%s+", "")
        attr['height'] = clean_height .. "px" 
      end
      
      return pandoc.Image({}, src, "", attr)
    end
  end
end
