function RawInline(el)
  if el.format == "html" and el.text:lower():match("^<img") then
    local src = el.text:match('src%s*=%s*["\']([^"\']+)["\']')
    local width = el.text:match('width%s*=%s*["\']([^"\']+)["\']')
    local height = el.text:match('height%s*=%s*["\']([^"\']+)["\']')
    
    if src then
      local attr = {}
      
      if width then 
        attr['width'] = width:gsub("px", "") 
      end
      if height then 
        attr['height'] = height:gsub("px", "") 
      end
      
      return pandoc.Image({}, src, "", attr)
    end
  end
end
