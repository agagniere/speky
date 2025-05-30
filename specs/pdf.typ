#import "@local/speky:0.0.4": speky, table_to_comments, table_to_requirements

#set document(title: [Speky --- Specifications], author: "Antoine GAGNIERE")

#align(center, text(size: 2em, weight: "bold")[
  _Speky_\
  Specifications
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
        table_to_requirements(csv("as_table.csv"), "functional"),
        table_to_comments(csv("comments/2025-05-27.csv")),
    ),
)
