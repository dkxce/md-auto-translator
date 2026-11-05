function RawInline(el)
  if el.format == "html" then
    local src = el.text:match('src="([^"]+)"')
    local width = el.text:match('width="([^"]+)"')
    local height = el.text:match('height="([^"]+)"')
    
    if src then
      local attr = {}
      if width then attr['width'] = width end
      if height then attr['height'] = height end
      return pandoc.Image({}, src, "", attr)
    end
  end
end
