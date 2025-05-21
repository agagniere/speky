#set document(
	 title: [Speky --- Specifications],
	 author: "Antoine GAGNIERE",
)
#show link: set text(fill: blue)
#show link: underline

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
	   	   let spec_list = specifications.at(category, default: ())
		   spec_list.push(spec)
		   specifications.insert(category, spec_list)
		   if "ref" in spec {
             for ref in spec.ref {
			   let ref_list = references.at(ref, default: ())
			   ref_list.push(spec)
			   references.insert(ref, ref_list)
			 }
		   }
	   }
	} else if data.kind == "tests" {
	  let category = data.category
	  for test in data.tests {
        let test_list = tests.at(category, default: ())
        test_list.push(test)
        tests.insert(category, test_list)
        for ref in test.ref {
		  let ref_list = testers.at(ref, default: ())
		  ref_list.push(test)
          testers.insert(ref, ref_list)
	    }
	  }
	}
  }

  [
	= Functional specifications
  	#for spec in specifications.at("functional") [
	  #let title = if "short" in spec {spec.id + " " + spec.short} else { spec.id }
	  == #title #label(spec.id)
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
	#pagebreak()
	= Functional tests
  	#for test in tests.at("functional") [
	  #let title = if "short" in test {test.id + " " + test.short} else { test.id }
	  == #title #label(test.id)
	  #test.long
	]
	#pagebreak()
	= Non-functional specifications
  	#for spec in specifications.at("non-functional") [
	  #let title = if "short" in spec {spec.id + " " + spec.short} else { spec.id }
	  == #title #label(spec.id)
	  #spec.long
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
 "tests/functional.yaml"
))
