#set document(
	 title: [Speky --- Specifications],
	 author: "Antoine GAGNIERE",
)
#show link: set text(fill: blue)
#show link: underline

#let get_title(something) = {
 if "short" in something {
  something.id + " " + something.short
 } else {
  something.id
 }
}

#let display_title(something) = [
 == #get_title(something) #label(something.id)
]

#let display_spec(spec, testers, references) = [
 #display_title(spec)
 #spec.long
 #if spec.id in testers [
  === Tested by
  #for test in testers.at(spec.id) [
   - #test.id
  ]
 ]
 #if spec.id in references [
  === Referenced by
  #for other in references.at(spec.id) [
   - #other.id
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
  for file in files {
    let data = yaml(file)
	if data.kind == "specifications" {
	   let category = data.category
	   for spec in data.requirements {
         specifications = append_at(specifications, category, spec)
         if "ref" in spec {
             for ref in spec.ref {
			   references = append_at(references, ref, spec)
			 }
		   }
	   }
	} else if data.kind == "tests" {
	  let category = data.category
	  for test in data.tests {
        tests = append_at(tests, category, test)
        for ref in test.ref {
		  testers = append_at(testers, ref, test)
	    }
	  }
	}
  }

  [
	= Functional specifications
  	#for spec in specifications.at("functional") {
	  display_spec(spec, testers, references)
	}
	#pagebreak()
	= Functional tests
  	#for test in tests.at("functional") [
	  #display_title(test)
	  #test.long
	  === Is a test for
	  #for r in test.ref [
	   - #r
	  ]
	]
	#pagebreak()
	= Non-functional specifications
  	#for spec in specifications.at("non-functional") {
     display_spec(spec, testers, references)
	}
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
 "tests/functional.yaml"
))
