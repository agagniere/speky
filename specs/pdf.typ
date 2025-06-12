#import "@local/speky:0.0.7": speky, table_to_comments

#set document(title: [Speky --- Specification], author: "Antoine GAGNIERE")

#align(center, text(size: 2em, weight: "bold")[
  _Speky_\
  Specification
])
#align(bottom, outline(depth: 2))
#pagebreak()

#set page(numbering: "1")

#speky(
  (
    "functional.yaml",
    "nonfunctional.yaml",
    "tests/functional.yaml",
    "tests/csv.yaml",
    "comments/2025-05-21.yaml",
    "comments/2025-05-23.yaml",
    "comments/2025-05-26.yaml",
    "comments/2025-05-30.yaml",
  ).map(yaml)
    + (
      "comments/2025-05-27.csv",
    ).map(f => table_to_comments(csv(f))),
)
