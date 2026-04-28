// ==========================================================================
//  Pandoc-Typst Template – Professionelles Dokument
//
//  Nutzung:
//    pandoc input.md --pdf-engine=typst --template=default.typ -o output.pdf
//
//  Unterstützte Frontmatter-Variablen (in der Markdown-Datei):
//    ---
//    title: "Mein Dokument"
//    subtitle: "Ein Untertitel"
//    author: "Max Mustermann"
//    date: "2026-03-25"
//    lang: de
//    abstract: "Kurze Zusammenfassung."
//    toc: true
//    mainfont: "Inter"
//    fontsize: 11pt
//    section-numbering: "1.1"
//    ---
// ==========================================================================

// ---------------------------------------------------------------------------
//  Farben – hier zentral anpassen
// ---------------------------------------------------------------------------
#let color-primary   = rgb("#2c3e50")
#let color-accent    = rgb("#3498db")
#let color-muted     = rgb("#7f8c8d")
#let color-light-bg  = rgb("#f8f9fa")
#let color-rule      = rgb("#dee2e6")

// ---------------------------------------------------------------------------
//  Hilfsfunktion: Content → String (für Kopf-/Fusszeile)
// ---------------------------------------------------------------------------
#let to-string(content) = {
  if content == none { return "" }
  if type(content) == str { return content }
  if content.has("text") { return content.text }
  if content.has("children") {
    return content.children.map(to-string).join("")
  }
  if content.has("body") { return to-string(content.body) }
  return ""
}

// ---------------------------------------------------------------------------
//  Syntax-Highlighting (von Pandoc generiert, falls vorhanden)
// ---------------------------------------------------------------------------
$if(highlighting-definitions)$
$highlighting-definitions$
$endif$

// ---------------------------------------------------------------------------
//  Definition-Listen
// ---------------------------------------------------------------------------
#show terms.item: it => block(breakable: false)[
  #text(weight: "bold")[#it.term]
  #block(inset: (left: 1.5em, top: -0.4em))[#it.description]
]

// ---------------------------------------------------------------------------
//  Blockquote-Funktion (Pandoc ≥3.2 gibt #blockquote[...] aus)
// ---------------------------------------------------------------------------
#let blockquote(body) = [
  #set text(style: "italic", fill: color-muted)
  #block(
    inset: (left: 1.5em, y: 0.5em),
    stroke: (left: 3pt + color-accent),
    body
  )
]

// ---------------------------------------------------------------------------
//  Horizontalrule-Funktion (Pandoc ≥3.2 gibt #horizontalrule[...] aus)
// ---------------------------------------------------------------------------
#let horizontalrule = []
// ---------------------------------------------------------------------------
//  Hauptfunktion
// ---------------------------------------------------------------------------
#let conf(
  title: none,
  subtitle: none,
  authors: (),
  date: none,
  abstract: none,
  abstract-title: none,
  keywords: (),
  lang: "de",
  region: "DE",
  font: ("Source Serif Pro", "Noto Sans", "Libertinus Serif"),
  font-heading: ("Source Sans Pro", "Noto Sans", "Noto Color Emoji","Libertinus Sans"),
  codefont: ("JetBrains Mono", "Fira Code", "Libertinus Mono"),
  mathfont: (),
  fontsize: 12pt,
  linestretch: 1.65,
  paper: "a4",
  margin: (top: 2.5cm, bottom: 2cm, left: 2.5cm, right: 2.5cm),
  cols: 1,
  sectionnumbering: none,
  pagenumbering: "1",
  linkcolor: none,
  citecolor: none,
  filecolor: none,
  thanks: none,
  doc,
) = {

  // -- Seitenformat --------------------------------------------------------
  set page(
    paper: paper,
    margin: margin,
    header: context {
      if counter(page).get().first() > 1 {
        set text(size: 8pt, fill: color-muted)
        if title != none { to-string(title) }
        h(1fr)
        if date != none { to-string(date) }
        v(2pt)
        line(length: 100%, stroke: 0.4pt + color-rule)
      }
    },
    footer: context {
      set text(size: 8pt, fill: color-muted)
      line(length: 100%, stroke: 0.4pt + color-rule)
      v(4pt)
      if authors.len() > 0 { to-string(authors.first().name) }
      h(1fr)
      if pagenumbering != none {
        counter(page).display(pagenumbering)
      }
    },
  )

  // -- Grundtypografie -----------------------------------------------------
  set text(
    font: font,
    size: fontsize,
    lang: lang,
    region: region,
    hyphenate: true,
  )

  set par(
    justify: true,
    leading: fontsize * linestretch - fontsize,
    first-line-indent: 0em,
    spacing: 0.8em,
  )

  // -- Überschriften -------------------------------------------------------
  if sectionnumbering != none {
    set heading(numbering: sectionnumbering)
  }

  show heading.where(level: 1): it => {
    v(1.2em)
    set text(size: 1.5em, weight: "bold", fill: color-primary, font: font-heading)
    it
    v(0.4em)
  }

  show heading.where(level: 2): it => {
    v(1em)
    set text(size: 1.2em, weight: "bold", fill: color-primary, font: font-heading)
    it
    v(0.3em)
  }

  show heading.where(level: 3): it => {
    v(0.8em)
    set text(size: 1.05em, weight: "semibold", fill: color-primary, font: font-heading)
    it
    v(0.2em)
  }

  // -- Links ---------------------------------------------------------------
  show link: set text(fill: color-accent)

  // -- Code (Inline) -------------------------------------------------------
  show raw.where(block: false): box.with(
    fill: color-light-bg,
    inset: (x: 3pt, y: 0pt),
    outset: (y: 3pt),
    radius: 2pt,
  )

  // -- Code (Block) --------------------------------------------------------
  show raw.where(block: true): block.with(
    fill: color-light-bg,
    inset: 10pt,
    radius: 4pt,
    width: 100%,
    stroke: 0.5pt + color-rule,
  )

  if codefont.len() > 0 {
    show raw: set text(font: codefont, size: 0.85em)
  }

  // -- Blockzitate ---------------------------------------------------------
  set quote(block: true)
  show quote: set pad(x: 1.5em)
  show quote: set text(style: "italic", fill: color-muted)

  // -- Tabellen ------------------------------------------------------------
  set table(
    inset: 8pt,
    stroke: (x: none, y: 0.5pt + color-rule),
  )
  show table.cell.where(y: 0): set text(weight: "bold")

  // -- Figuren-Beschriftungen ----------------------------------------------
  show figure.where(kind: table): set figure.caption(position: top)
  show figure.where(kind: image): set figure.caption(position: bottom)

  // -----------------------------------------------------------------------
  //  Titelseite
  // -----------------------------------------------------------------------
  if title != none {
    v(2fr)
    align(left)[
      #block(text(size: 2.4em, weight: "bold", fill: color-primary, title))
      #if subtitle != none {
        v(0.3em)
        block(text(size: 1.3em, fill: color-muted, subtitle))
      }
      #v(1em)
      #line(length: 40%, stroke: 2pt + color-accent)
      #v(1em)
      #if authors.len() > 0 {
        for author in authors {
          block(spacing: 0.5em)[
            #text(size: 1.1em, weight: "medium")[#author.name]
            #if to-string(author.affiliation) != "" {
              linebreak()
              text(size: 0.9em, fill: color-muted)[#author.affiliation]
            }
            #if to-string(author.email) != "" {
              linebreak()
              text(size: 0.9em, fill: color-accent)[#author.email]
            }
          ]
        }
      }
      #if date != none {
        v(0.5em)
        text(size: 1em, fill: color-muted, date)
      }
    ]
    v(3fr)

    if abstract != none {
      line(length: 100%, stroke: 0.5pt + color-rule)
      v(0.5em)
      set text(size: 0.95em)
      if abstract-title != none {
        text(weight: "bold", abstract-title)
        parbreak()
      } else {
        text(weight: "bold")[Zusammenfassung]
        parbreak()
      }
      abstract
      v(0.5em)
      line(length: 100%, stroke: 0.5pt + color-rule)
    }

    if keywords.len() > 0 {
      v(0.3em)
      text(size: 0.85em, fill: color-muted)[
        *Schlagwörter:* #keywords.join(", ")
      ]
    }

    pagebreak()
  }

  // -----------------------------------------------------------------------
  //  Inhalt
  // -----------------------------------------------------------------------
  if cols > 1 {
    columns(cols, doc)
  } else {
    doc
  }
}

// =========================================================================
//  Pandoc-Boilerplate
//  Ab hier setzt Pandoc die Metadaten und den Dokumentinhalt ein.
// =========================================================================

$for(header-includes)$
$header-includes$
$endfor$

#show: doc => conf(
$if(title)$
  title: [$title$],
$endif$
$if(subtitle)$
  subtitle: [$subtitle$],
$endif$
$if(author)$
  authors: (
$for(author)$
$if(author.name)$
    ( name: [$author.name$],
      affiliation: [$author.affiliation$],
      email: [$author.email$] ),
$else$
    ( name: [$author$],
      affiliation: "",
      email: "" ),
$endif$
$endfor$
  ),
$endif$
$if(keywords)$
  keywords: ($for(keywords)$"$keywords$",$endfor$),
$endif$
$if(date)$
  date: [$date$],
$endif$
$if(lang)$
  lang: "$lang$",
$endif$
$if(region)$
  region: "$region$",
$endif$
$if(abstract-title)$
  abstract-title: [$abstract-title$],
$endif$
$if(abstract)$
  abstract: [$abstract$],
$endif$
$if(margin)$
  margin: ($for(margin/pairs)$$margin.key$: $margin.value$,$endfor$),
$endif$
$if(papersize)$
  paper: "$papersize$",
$endif$
$if(mainfont)$
  font: ("$mainfont$",),
$endif$
$if(fontsize)$
  fontsize: $fontsize$,
$endif$
$if(codefont)$
  codefont: ($for(codefont)$"$codefont$",$endfor$),
$endif$
$if(linestretch)$
  linestretch: $linestretch$,
$endif$
$if(section-numbering)$
  sectionnumbering: "$section-numbering$",
$endif$
  pagenumbering: $if(page-numbering)$"$page-numbering$"$else$"1"$endif$,
  cols: $if(columns)$$columns$$else$1$endif$,
  doc,
)

$for(include-before)$
$include-before$
$endfor$

$if(toc)$
#outline(
  title: auto,
  depth: $if(toc-depth)$$toc-depth$$else$3$endif$,
)
#pagebreak()
$endif$

$body$

$if(citations)$
$for(nocite-ids)$
#cite(label("${it}"), form: none)
$endfor$
$if(csl)$
#set bibliography(style: "$csl$")
$elseif(bibliographystyle)$
#set bibliography(style: "$bibliographystyle$")
$endif$
$if(bibliography)$
#bibliography(($for(bibliography)$"$bibliography$"$sep$,$endfor$)$if(full-bibliography)$, full: true$endif$)
$endif$
$endif$

$for(include-after)$
$include-after$
$endfor$
