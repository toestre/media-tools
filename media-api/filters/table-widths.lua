-- table-widths.lua
-- Reads width hints from HTML comments preceding tables, e.g.:
-- <!-- table: cols=[0.1, 0.5, 0.4] total=0.85 -->

local pending_widths = nil
local pending_total = nil
local pending_align = nil

-- Parse a comment like: table: cols=[0.1, 0.5, 0.4] total=0.85
local function parse_hint(text)
  local normalized = text
    :gsub("^%s*<!%-%-%s*", "")
    :gsub("%s*%-%->%s*$", "")
  local s = normalized:match("^%s*table:%s*(.+)$")
  if not s then
    return nil, nil
  end

  local cols = {}
  local cols_str = s:match("cols=%[([^%]]+)%]")
  if cols_str then
    for v in cols_str:gmatch("[%d%.]+") do
      cols[#cols + 1] = tonumber(v)
    end
  end

  local total = tonumber(s:match("total=([%d%.]+)"))
  local align = s:match("align=([%a]+)")
  if align then
    align = align:lower()
    if align ~= "left" and align ~= "center" and align ~= "right" then
      align = nil
    end
  end

  return (#cols > 0 and cols or nil), total, align
end

-- Convert a Pandoc Alignment to a Typst align string
local function pandoc_align_to_typst(align)
  local align_name = tostring(align)
  if align_name == "AlignLeft" then
    return "left"
  elseif align_name == "AlignRight" then
    return "right"
  elseif align_name == "AlignCenter" then
    return "center"
  end
  return "left"
end

local function escape_typst_text(text)
  local escaped = text
  escaped = escaped:gsub("\\", "\\\\")
  escaped = escaped:gsub("#", "\\#")
  escaped = escaped:gsub("%[", "\\[")
  escaped = escaped:gsub("%]", "\\]")
  return escaped
end

local function render_inline(inline)
  if inline.t == "Str" then
    return escape_typst_text(inline.text)
  elseif inline.t == "Space" then
    return " "
  elseif inline.t == "SoftBreak" or inline.t == "LineBreak" then
    return "\n"
  elseif inline.t == "Strong" then
    return "*" .. render_inlines(inline.content) .. "*"
  elseif inline.t == "Emph" then
    return "_" .. render_inlines(inline.content) .. "_"
  elseif inline.t == "Code" then
    return "`" .. (inline.text or "") .. "`"
  elseif inline.t == "RawInline" then
    if inline.format == "typst" then
      return inline.text
    end
    return escape_typst_text(inline.text or "")
  elseif inline.t == "Link" then
    local label = render_inlines(inline.content)
    local raw_target = inline.target or ""
    if raw_target:match("^<[^>]+>$") then
      return "#link(" .. raw_target .. ")[" .. label .. "]"
    end
    local target = escape_typst_text(raw_target)
    return '#link("' .. target .. '")[' .. label .. "]"
  end

  return escape_typst_text(pandoc.utils.stringify({ inline }))
end

-- Render a single Pandoc Inline list to Typst markup
function render_inlines(inlines)
  local parts = {}
  for _, inline in ipairs(inlines) do
    parts[#parts + 1] = render_inline(inline)
  end
  return table.concat(parts)
end

-- Render a cell (list of blocks) to a Typst cell string
local function blocks_to_typst_cell(blocks)
  local parts = {}
  for _, blk in ipairs(blocks) do
    if blk.t == "Para" or blk.t == "Plain" then
      parts[#parts + 1] = render_inlines(blk.content)
    end
  end
  return table.concat(parts, "\\n")
end

-- Build a raw Typst table block
local function build_typst_table(tbl, col_widths, total_width, table_align)
  local col_specs = tbl.colspecs
  local head = tbl.head
  local bodies = tbl.bodies
  local ncols = #col_specs

  local fracs = {}
  if col_widths and #col_widths == ncols then
    local sum = 0
    for _, value in ipairs(col_widths) do
      sum = sum + value
    end
    for _, value in ipairs(col_widths) do
      fracs[#fracs + 1] = value / sum
    end
  else
    for i = 1, ncols do
      fracs[i] = 1 / ncols
    end
  end

  local tw = total_width or 1.0
  local width_percent = tw * 100
  local block_align = table_align
  if not block_align then
    if tw < 1.0 then
      block_align = "center"
    else
      block_align = "left"
    end
  end

  local col_defs = {}
  for _, fraction in ipairs(fracs) do
    col_defs[#col_defs + 1] = string.format("%.4ffr", fraction)
  end
  local columns_str = table.concat(col_defs, ", ")

  local aligns = {}
  for _, col_spec in ipairs(col_specs) do
    aligns[#aligns + 1] = pandoc_align_to_typst(col_spec[1])
  end

  local function render_rows(rows, is_header)
    local lines = {}
    for _, row in ipairs(rows) do
      for column_index, cell in ipairs(row.cells) do
        local text = blocks_to_typst_cell(cell.content)
        local align = aligns[column_index] or "left"
        if is_header then
          lines[#lines + 1] = string.format(
            "  table.cell(align: %s)[*%s*],",
            align,
            text
          )
        else
          lines[#lines + 1] = string.format(
            "  table.cell(align: %s)[%s],",
            align,
            text
          )
        end
      end
    end
    return table.concat(lines, "\n")
  end

  local header_lines = ""
  if head and head.rows and #head.rows > 0 then
    header_lines = render_rows(head.rows, true)
  end

  local body_lines_parts = {}
  for _, body in ipairs(bodies) do
    if body.body then
      body_lines_parts[#body_lines_parts + 1] = render_rows(body.body, false)
    end
  end
  local body_lines = table.concat(body_lines_parts, "\n")

  local header_block = ""
  if header_lines ~= "" then
    header_block = "  table.header(\n" .. header_lines .. "\n  ),"
  end

  local typst = string.format(
    [[
#align(%s, block(width: %.2f%%)[
#table(
  columns: (%s),
  stroke: (x: none, y: 0.5pt),
  inset: 6pt,
  fill: (col, row) => if row == 0 { luma(230) } else { white },
%s
%s
)
])
]],
    block_align,
    width_percent,
    columns_str,
    header_block,
    body_lines
  )

  return typst
end

-- Filter: walk Blocks, watch for RawBlock HTML comments then Tables
function Blocks(blocks)
  local result = {}
  local i = 1
  while i <= #blocks do
    local blk = blocks[i]

    -- Detect hint comment
    if blk.t == "RawBlock" and blk.format == "html" then
      local cols, total, align = parse_hint(blk.text)
      if cols or total or align then
        pending_widths = cols
        pending_total = total
        pending_align = align
        -- swallow the comment block (don't emit it)
        i = i + 1
        goto continue
      end
    end

    -- Intercept Table
    if blk.t == "Table" and (pending_widths or pending_total or pending_align) then
      local typst_src = build_typst_table(
        blk,
        pending_widths,
        pending_total,
        pending_align
      )
      result[#result + 1] = pandoc.RawBlock("typst", typst_src)
      pending_widths = nil
      pending_total = nil
      pending_align = nil
      i = i + 1
      goto continue
    end

    -- Otherwise reset pending state (non-table block broke the sequence)
    if blk.t ~= "RawBlock" then
      pending_widths = nil
      pending_total = nil
      pending_align = nil
    end

    result[#result + 1] = blk
    i = i + 1
    ::continue::
  end
  return result
end
