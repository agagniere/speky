#set document(
	 title: [Speky --- Specifications],
	 author: "Antoine GAGNIERE",
)
#show link: set text(fill: blue)
#show link: underline

#let render(file, heading_depth: 1) = {
  let data = yaml(file)
  for spec in data.requirements [
   #let title = if "short" in spec { spec.id + " " + spec.short } else { spec.id }
   == #title
   #spec.long
  ]
}

#align(
  center,
  text(size: 2em, weight: "bold")[
    _Speky_\
	Specifications
  ],
)
#align(bottom, outline(depth: 2))
#pagebreak()

#set page(numbering: "1")

= Functional requirements
#render("functional.yaml")

#pagebreak()
= Non-functional requirements
#render("nonfunctional.yaml")
