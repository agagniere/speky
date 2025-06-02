#let string_to_bool(string) = {
  string == "true"
}

#let table_to_dict_list(table, transform: (:)) = {
  let result = ()
  for row in table.slice(1) {
    let obj = (:)
    for (name, value) in table.at(0).zip(row) {
      if name in transform {
        obj.insert(name, transform.at(name)(value))
      } else {
        obj.insert(name, value)
      }
    }
    result.push(obj)
  }
  return result
}

#let table_to_requirements(table, category) = {
  (
    "kind": "requirements",
    "category": category,
    "requirements": table_to_dict_list(table),
  )
}

#let table_to_comments(table) = {
  (
    "kind": "comments",
    "comments": table_to_dict_list(table, transform: (
      "external": string_to_bool,
    )),
  )
}
