local diagram_index = 0
local dropped_title = false

local function has_class(classes, name)
  for _, class in ipairs(classes) do
    if class == name then
      return true
    end
  end
  return false
end

local function tex_escape(value)
  local replacements = {
    ["\\"] = "\\textbackslash{}",
    ["{"] = "\\{",
    ["}"] = "\\}",
    ["$"] = "\\$",
    ["&"] = "\\&",
    ["#"] = "\\#",
    ["_"] = "\\_",
    ["%"] = "\\%",
    ["~"] = "\\textasciitilde{}",
    ["^"] = "\\textasciicircum{}",
  }
  return (value:gsub("[\\{}$&#_%%~^]", replacements))
end

local function plantuml_title(source)
  for line in source:gmatch("[^\r\n]+") do
    local title = line:match("^%s*title%s+(.+)%s*$")
    if title and title ~= "" then
      return title
    end
  end
  return nil
end

local function is_manual_heading_number(value)
  local normalized = value:gsub("%.$", "")
  if normalized == "" then
    return false
  end
  if normalized:match("[^%d%.]") then
    return false
  end
  if normalized:match("^%.") or normalized:match("%.$") or normalized:match("%.%.") then
    return false
  end
  return normalized:match("%d") ~= nil
end

local function cell_to_latex(cell)
  local values = {}
  for _, block in ipairs(cell) do
    values[#values + 1] = tex_escape(pandoc.utils.stringify(block))
  end
  return table.concat(values, "\\par ")
end

local function first_column_width(headers)
  local first_header = headers[1] and cell_to_latex(headers[1]) or ""
  if first_header == "环境变量" then
    return "6.0cm"
  end
  return "2.4cm"
end

local function header_text(headers, index)
  return headers[index] and cell_to_latex(headers[index]) or ""
end

local function fixed_column_width(headers, index)
  if index == 1 then
    return first_column_width(headers)
  end
  if header_text(headers, index) == "优先级" then
    return "1.5cm"
  end
  return nil
end

local function column_alignment(headers, index)
  if header_text(headers, index) == "优先级" then
    return "\\centering"
  end
  return "\\raggedright"
end

local function table_colspec(count, headers)
  local widths = {}
  local fixed_widths = {}
  local flex_count = 0

  for index = 1, count do
    widths[index] = fixed_column_width(headers, index)
    if widths[index] then
      fixed_widths[#fixed_widths + 1] = widths[index]
    else
      flex_count = flex_count + 1
    end
  end

  local flex_width = nil
  if flex_count > 0 then
    local fixed_expr = ""
    for _, width in ipairs(fixed_widths) do
      fixed_expr = fixed_expr .. "-" .. width
    end
    flex_width = string.format(
      "\\dimexpr(\\linewidth%s-%d\\tabcolsep-%d\\arrayrulewidth)/%d\\relax",
      fixed_expr,
      count * 2,
      count + 1,
      flex_count
    )
  end

  local cols = {}
  for index = 1, count do
    cols[#cols + 1] = "|>{" .. column_alignment(headers, index) .. "\\arraybackslash}p{" .. (widths[index] or flex_width) .. "}"
  end

  return table.concat(cols, "") .. "|"
end

local function table_row(cells)
  local values = {}
  for _, cell in ipairs(cells) do
    values[#values + 1] = cell_to_latex(cell)
  end
  return table.concat(values, " & ") .. "\\tabularnewline"
end

function Header(el)
  if el.level == 1 and not dropped_title then
    dropped_title = true
    return {}
  end

  if el.level > 1 then
    el.level = el.level - 1
  end

  local first = el.content[1]
  if first and first.text and is_manual_heading_number(first.text) then
    table.remove(el.content, 1)
    if el.content[1] and el.content[1].t == "Space" then
      table.remove(el.content, 1)
    end
  end

  return el
end

function Table(el)
  local col_count = #el.headers
  if col_count == 0 and #el.rows > 0 then
    col_count = #el.rows[1]
  end

  local latex = {
    "\\begin{longtable}{" .. table_colspec(col_count, el.headers) .. "}",
    "\\hline",
  }

  if #el.headers > 0 then
    latex[#latex + 1] = table_row(el.headers)
    latex[#latex + 1] = "\\hline"
    latex[#latex + 1] = "\\endhead"
  end

  for _, row in ipairs(el.rows) do
    latex[#latex + 1] = table_row(row)
    latex[#latex + 1] = "\\hline"
  end

  latex[#latex + 1] = "\\end{longtable}"

  return pandoc.RawBlock("latex", table.concat(latex, "\n"))
end

function CodeBlock(el)
  if not has_class(el.classes, "plantuml") then
    return el
  end

  diagram_index = diagram_index + 1

  local basename = string.format("plantuml-diagrams/req-uml-%02d", diagram_index)
  local caption = plantuml_title(el.text) or string.format("PlantUML 图 %02d", diagram_index)

  local latex = table.concat({
    "\\begin{figure}[H]",
    "\\centering",
    "\\begin{adjustbox}{max width=\\linewidth,max totalheight=0.78\\textheight,center}",
    "\\begingroup",
    "\\renewcommand{\\PlantUMLJobname}{" .. basename .. "}",
    "\\begin{plantuml}",
    el.text,
    "\\end{plantuml}",
    "\\endgroup",
    "\\end{adjustbox}",
    "\\caption{" .. tex_escape(caption) .. "}",
    "\\end{figure}",
  }, "\n")

  return pandoc.RawBlock("latex", latex)
end
