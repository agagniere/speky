#import "conversions.typ": table_to_comments, table_to_requirements
#import "requirement.typ": display_requirement
#import "common.typ": append_at, display_title, link_to
#import "@preview/suboutline:0.3.0": suboutline

#let speky(files) = {
  let references = (:)
  let testers = (:)
  let specifications = (:)
  let tests = (:)
  let comments = (:)
  let by_id = (:)
  let tags = (:)

  for data in files {
    if data.kind == "requirements" {
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
    = Requirements
    #suboutline(depth: 2)
    #pagebreak()
    #for (cat, specs) in specifications.pairs().sorted() [
      == #upper(cat.at(0))#lower(cat.slice(1))
      #for spec in specs {
        display_requirement(spec, testers, references, comments, by_id)
      }
    ]
    #pagebreak()
    = Tests
    #suboutline(depth: 2)
    #pagebreak()
    #for (cat, _tests) in tests.pairs().sorted() [
      == #upper(cat.at(0))#lower(cat.slice(1))
      #for test in _tests [
        #display_title(test, supplement: "Test")
        #label(test.id)
        #test.long

        #if test.ref.len() == 1 [
          *Is a test for* #link_to(by_id.at(test.ref.at(0)))
        ] else [
          ==== Is a test for
          #for r in test.ref [
            - #link_to(by_id.at(r))
          ]
        ]
        ==== Initial state
        #if "initial" in test [
          #test.initial
        ]
        #if "prereq" in test [
          The expected state is the final state of
          #if test.prereq.len() == 1 {
            link_to(by_id.at(test.prereq.at(0)))
          } else {
            for prereq in test.prereq [
              - #link_to(by_id.at(prereq))
            ]
          }
        ]
        ==== Procedure
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
        #if test.id in comments [
          ==== Comments
          #for comment in comments.at(test.id) {
            let external = ("external" in comment) and comment.external
            align(
              if external { left } else { right },
              box(
                grid(
                  align(left, strong(comment.from)),
                  align(right, text(comment.date, fill: rgb("#999"))),
                  grid.cell(eval(comment.text, mode: "markup"), colspan: 2),
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
    ]
    #if tags.len() > 0 [
      #pagebreak()
      = Requirements by tag
      #for (tag, specs) in tags.pairs().sorted() [
        #heading(level: 2)[#upper(tag.at(0))#lower(tag.slice(1))]
        #label(tag)
        #for spec in specs {
          list.item(link_to(spec))
        }
      ]
    ]
  ]
}
