#set document(title: [Speky --- Specifications], author: "Antoine GAGNIERE")

#let get_title(something) = {
  if "short" in something {
    raw(something.id) + " " + something.short
  } else {
    raw(something.id)
  }
}

#let display_title(something, supplement: "Requirement") = {
  heading(get_title(something), level: 2, supplement: supplement)
}

#let link_to(something) = {
  link(label(something.id), underline(text(get_title(something), fill: blue)))
}

#let display_spec(spec, testers, references, comments, by_id) = [
  #display_title(spec)
  #label(spec.id)
  #if "tags" in spec {
    for tag in spec.tags {
      link(label(tag), box(tag, fill: rgb("#7d9"), inset: 3pt, radius: 10pt))
      text(" ")
    }
    linebreak()
  }
  #eval(spec.long, mode: "markup")

  #if spec.id in testers {
    let tests = testers.at(spec.id)
    if tests.len() == 1 [
      *Tested by* #link_to(tests.at(0))
    ] else [
      === Tested by
      #for test in tests [
        - #link_to(test)
      ]

    ]
  }

  #if spec.id in references {
    let refs = references.at(spec.id)
    if refs.len() == 1 [
      *Referenced by* #link_to(refs.at(0))
    ] else [
      === Referenced by
      #for other in refs [
        - #link_to(other)
      ]
    ]
  }

  #if "ref" in spec {
    if spec.ref.len() == 1 [
      *Relates to* #link_to(by_id.at(spec.ref.at(0)))
    ] else [
      === Relates to
      #for other in spec.ref [
        - #link_to(by_id.at(other))
      ]
    ]
  }

  #if spec.id in comments [
    === Comments
    #for comment in comments.at(spec.id) {
      let external = ("external" in comment) and comment.external
      align(
        if external { left } else { right },
        box(
          grid(
            align(left, strong(comment.from)),
            align(right, text(comment.date, fill: rgb("#999"))),
            grid.cell(eval(comment.text, mode: "markup"), colspan: 2),
            columns: (1fr, 1fr),
            gutter: 8pt
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

#let append_at(map, key, value) = {
  let present = map.at(key, default: ())
  present.push(value)
  map.insert(key, present)
  map
}

#let speky(files) = {
  let references = (:)
  let testers = (:)
  let specifications = (:)
  let tests = (:)
  let comments = (:)
  let by_id = (:)
  let tags = (:)

  for file in files {
    let data = yaml(file)
    if data.kind == "specifications" {
      let category = data.category
      for spec in data.requirements {
        by_id.insert(spec.id, spec)
        specifications = append_at(specifications, category, spec)
        if "ref" in spec {
          for ref in spec.ref {
            references = append_at(references, ref, spec)
          }
        }
        if "tags" in spec {
          for tag in spec.tags {
            tags = append_at(tags, tag, spec)
          }
        }
      }
    } else if data.kind == "tests" {
      let category = data.category
      for test in data.tests {
        by_id.insert(test.id, test)
        tests = append_at(tests, category, test)
        for ref in test.ref {
          testers = append_at(testers, ref, test)
        }
      }
    } else if data.kind == "comments" {
      let default = data.at("default", default: (:))
      if "external" not in default {
        default.external = false
      }
      for comment in data.comments {
        for field in ("date", "from", "about", "external") {
          if field not in comment {
            comment.insert(field, default.at(field))
          }
        }
        comments = append_at(comments, comment.about, comment)
      }
    }
  }

  [
    #heading()[Functional specifications]
    #for spec in specifications.at("functional") {
      display_spec(spec, testers, references, comments, by_id)
    }
    #pagebreak()
    #heading()[Functional tests]
    #for test in tests.at("functional") [
      #display_title(test, supplement: "Test")
      #label(test.id)
      #test.long

      #if test.ref.len() == 1 [
        *Is a test for* #link_to(by_id.at(test.ref.at(0)))
      ] else [
        === Is a test for
        #for r in test.ref [
          - #link_to(by_id.at(r))
        ]
      ]
      === Initial state
      #if "initial" in test [
        #test.initial
      ]
      #if "prereq" in test [
        The expected state is the final state of tests:
        #for prereq in test.prereq [
          - #link_to(by_id.at(prereq))
        ]
      ]
      === Procedure
      #for step in test.steps {
        enum.item()[
          #eval(step.action, mode: "markup")
          #if ("run" in step) or ("sample" in step) {
            block(
              {
                if "run" in step {
                  raw("$ ")
                  raw(step.run.trim(), lang: "bash")
                  linebreak()
                }
                if "expected" in step {
                  text(raw(step.expected), fill: rgb("#999"))
                }
                if "sample" in step {
                  raw(step.sample, lang: step.at(
                    "sample_lang",
                    default: "text",
                  ))
                }
              },
              fill: rgb("#f5f5f5"),
              inset: 8pt,
              radius: 8pt,
            )
            linebreak()
          }
        ]
      }
      #pagebreak(weak: true)
    ]
    #if "non-functional" in specifications [
      #pagebreak()
      = Non-functional specifications
      #for spec in specifications.at("non-functional") {
        display_spec(spec, testers, references, comments, by_id)
      }
    ]
    #if tags.len() > 0 [
      #pagebreak()
      = Requirements by tag
      #for (tag, specs) in tags.pairs() [
        #heading(level: 2)[#upper(tag.at(0))#lower(tag.slice(1))]
        #label(tag)
        #for spec in specs {
          list.item(link_to(spec))
        }
      ]
    ]
  ]
}

#align(center, text(size: 2em, weight: "bold")[
  _Speky_\
  Specifications
])
#align(bottom, outline(depth: 2))
#pagebreak()

#set page(numbering: "1")

#speky((
  "functional.yaml",
  "nonfunctional.yaml",
  "tests/functional.yaml",
  "comments/2025-05-21.yaml",
  "comments/2025-05-23.yaml",
))
