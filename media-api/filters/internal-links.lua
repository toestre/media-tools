-- internal-links.lua
function Link(el)
    local target = el.target
    if target:sub(1,1) == "#" then
      local label = target:sub(2)
      el.target = "<" .. label .. ">"
      return el
    end
  end