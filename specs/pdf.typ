#import "@local/speky:0.0.3": speky

#set document(title: [Speky --- Specifications], author: "Antoine GAGNIERE")

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
  "comments/2025-05-26.yaml",
).map(yaml))
