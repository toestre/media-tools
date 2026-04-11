#set text(
$if(mainfont)$
  font: ("$mainfont$",),
$endif$
)

#set page(
$if(papersize)$
  paper: "$papersize$",
$endif$
$if(margin)$
  margin: ($for(margin/pairs)$$margin.key$: $margin.value$,$endfor$),
$endif$
)

$if(toc)$
#outline(
  title: auto,
  depth: none
);
$endif$

$for(header-includes)$
$header-includes$

$endfor$
$for(include-before)$
$include-before$

$endfor$

$body$

$for(include-after)$

$include-after$
$endfor$
