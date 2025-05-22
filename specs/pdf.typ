z#set document(
	title: [Speky --- Specifications],
	author: "Antoine GAGNIERE",
)
#show link: set text(fill: blue)
#show link: underline

#let get_title(something) = {
    if "short" in something {
        raw(something.id) + " " + something.short
    } else {
        raw(something.id)
    }
}

#let display_title(something) = [
    == #get_title(something) #label(something.id)
]

#let display_spec(spec, testers, references, comments) = [
    #display_title(spec)
    #spec.long
    #if spec.id in testers [
        === Tested by
        #for test in testers.at(spec.id) [
            - #get_title(test)
        ]
    ]
    #if spec.id in references [
        === Referenced by
        #for other in references.at(spec.id) [
            - #get_title(other)
        ]
    ]
    #if spec.id in comments [
        === Comments
        #for comment in comments.at(spec.id) [
            - #comment.text
        ]
    ]
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
	        for comment in data.comments {
	            comments = append_at(comments, comment.about, comment)
	        }
	    }
    }

    [
	    = Functional specifications
        #for spec in specifications.at("functional") {
	        display_spec(spec, testers, references, comments)
	    }
	    #pagebreak()
	    = Functional tests
        #for test in tests.at("functional") [
	        #display_title(test)
	        #test.long
	        === Is a test for
	        #for r in test.ref [
	            - #get_title(by_id.at(r))
	        ]
	        === Initial state
	        #if "initial" in test [
	            #test.initial
	        ]
	        #if "prereq" in test [
	            The expected state is the final state of tests:
                #for prereq in test.prereq [
                    - #get_title(by_id.at(prereq))
		        ]
	        ]
	        === Procedure
	        #enum(tight: false,
	            for step in test.steps {
	                enum.item()[
	                    #step.action\
	                    #if "run" in step [
	                        #raw(step.run.trim(), block: false, lang: "bash")\
	                    ]
	                    #if "sample" in step {
	                        block(
                                fill: rgb("#ddd"),
                                inset: 8pt,
                                radius: 5pt,
                                text(
	                                raw(step.sample, block: false, lang: "yaml")
		                        ))
	                    }
	                    #if "expected" in step [
	                        #raw(step.expected, block: false)
	                    ]
	                ]
	            }
	        )

	    ]
	    #if "non-functional" in specifications [
	        #pagebreak()
	        = Non-functional specifications
            #for spec in specifications.at("non-functional") {
                display_spec(spec, testers, references, comments)
	        }
	    ]
	    #if tags.len() > 0 [
	        #pagebreak()
	        = Requirements by tag
	        #for (tag, specs) in tags.pairs() [
	            == #upper(tag.at(0))#lower(tag.slice(1))
	            #for spec in specs [
	                - #get_title(spec)
	            ]
	        ]
	    ]
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

#speky((
    "functional.yaml",
    "nonfunctional.yaml",
    "tests/functional.yaml",
    "comments/2025-05-21.yaml"
))
