#let get_title(something) = {
  if "short" in something {
    raw(something.id) + " " + something.short
  } else {
    raw(something.id)
  }
}

#let display_title(something, level: 2, supplement: "Requirement") = {
  heading(get_title(something), level: level, supplement: supplement)
}

#let link_to(something) = {
  link(label(something.id), underline(text(get_title(something), fill: blue)))
}

#let append_at(map, key, value) = {
  let present = map.at(key, default: ())
  present.push(value)
  map.insert(key, present)
  return map
}
