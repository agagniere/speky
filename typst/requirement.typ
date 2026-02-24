#import "common.typ": display_title, link_to

#let display_requirement(req, testers, references, comments, by_id) = [
  #display_title(req)
  #label(req.id)

  #if "tags" in req {
    for tag in req.tags {
      if tag.contains(":") {
        let index = tag.position(":")
        let group = tag.slice(0, index)
        let subtag = tag.slice(index + 1)
        link(label(tag), {
          box(inset: 3pt, radius: 10pt, stroke: rgb("#7d9"))[
            #box(
              fill: rgb("#7d9"),
              outset: (left: 3pt, top: 3pt, bottom: 3pt, right: 1.5pt),
              radius: (left: 10pt),
              group,
            )
            #subtag
          ]
        })
      } else {
        link(label(tag), box(
          fill: rgb("#7d9"),
          inset: 3pt,
          radius: 10pt,
          outset: 0.5pt,
        )[#tag])
      }
      text(" ")
    }
    linebreak()
  }

  #if "client_statement" in req {
    block(
      eval(req.client_statement, mode: "markup"),
      fill: rgb("#eee"),
      breakable: false,
      inset: 10pt,
      radius: 3pt,
      stroke: ("left": 5pt + rgb("#888")),
    )
  }

  #eval(req.long, mode: "markup")

  #if "properties" in req [
    ==== Properties
    #for (key, value) in req.properties.pairs().sorted() [
      - *#key*: #eval(str(value), mode: "markup")
    ]
  ]

  #if req.id in testers {
    let tests = testers.at(req.id)
    if tests.len() == 1 [
      *Tested by* #link_to(tests.at(0))
    ] else [
      ==== Tested by
      #for test in tests.sorted(key: r => r.id) [
        - #link_to(test)
      ]

    ]
  }

  #if req.id in references {
    let refs = references.at(req.id)
    if refs.len() == 1 [
      *Referenced by* #link_to(refs.at(0))
    ] else [
      ==== Referenced by
      #for other in refs.sorted(key: r => r.id) [
        - #link_to(other)
      ]
    ]
  }

  #if "ref" in req {
    if req.ref.len() == 1 [
      *Relates to* #link_to(by_id.at(req.ref.at(0)))
    ] else [
      ==== Relates to
      #for other in req.ref.sorted() [
        - #link_to(by_id.at(other))
      ]
    ]
  }

  #if req.id in comments [
    ==== Comments
    #for comment in comments.at(req.id) {
      let external = ("external" in comment) and comment.external
      align(
        if external { left } else { right },
        box(
          grid(
            align(left, strong(comment.from)),
            align(right, text(comment.date, fill: rgb("#999"))),
            grid.cell(
              align(left, eval(comment.text, mode: "markup")),
              colspan: 2,
            ),
            columns: (1fr, 1fr),
            gutter: 8pt,
          ),
          width: 80%,
          inset: 5pt,
          radius: 5pt,
          fill: if external { rgb("#eee") } else { rgb("#eef") },
        ),
      )
    }
  ]
  #pagebreak(weak: true)
]
