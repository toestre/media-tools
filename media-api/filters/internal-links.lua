-- internal-links.lua
local function escape_typst_text(text)
  local escaped = text
  escaped = escaped:gsub("\\", "\\\\")
  escaped = escaped:gsub("#", "\\#")
  escaped = escaped:gsub("%[", "\\[")
  escaped = escaped:gsub("%]", "\\]")
  return escaped
end

function Link(el)
  local target = el.target or ""
  if target:sub(1, 1) ~= "#" then
    return nil
  end

  local label = target:sub(2)
  local text = escape_typst_text(pandoc.utils.stringify(el.content))
  return pandoc.RawInline("typst", "#link(<" .. label .. ">)[" .. text .. "]")
end