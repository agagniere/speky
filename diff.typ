// Source: https://gist.github.com/Dragonink/2c50e4b9ed8ba071060f15b1977aa05c

#let diff-box(color, contents) = box(
  outset: 0.25em,
  fill: color.transparentize(85%),
  text(fill: color, contents),
)

#let INSERT_RE = regex(`\{\+{2}(.+?)\+{2}\}`.text)
#show INSERT_RE: this => {
  let (contents,) = this.text.match(INSERT_RE).captures
  diff-box(green, underline(contents))
}

#let DELETE_RE = regex(`\{(?:-{2}|–)(.+?)(?:-{2}|–)\}`.text)
#show DELETE_RE: this => {
  let (contents,) = this.text.match(DELETE_RE).captures
  diff-box(red, strike(contents))
}

#let REPLACE_RE = regex(`\{(?:~{2})(.+?)~>(.+?)(?:~{2})\}`.text)
#show REPLACE_RE: this => {
  let (old, new) = this.text.match(REPLACE_RE).captures
  diff-box(orange)[
    #strike(old)
    #underline(new)
  ]
}

#include "diff.content.typ"
