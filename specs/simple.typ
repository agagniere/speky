#import "@local/speky:0.0.4": speky, table_to_comments, table_to_requirements, get_title, no_eval

#set document(title: [Speky --- Specifications], author: "Antoine GAGNIERE")

#align(center, text(size: 2em, weight: "bold")[
  _Speky_\
  Specifications
])
#align(bottom, outline(depth: 2))
#pagebreak()

#speky(
  (
    "functional.yaml",
    "nonfunctional.yaml",
    "tests/functional.yaml",
    "tests/csv.yaml",
    "comments/2025-05-21.yaml",
    "comments/2025-05-23.yaml",
    "comments/2025-05-26.yaml",
  ).map(yaml)
    + (
        table_to_requirements(csv("as_table.csv"), "functional"),
        table_to_comments(csv("comments/2025-05-27.csv")),
    ),
    f_link: get_title,
    f_eval: no_eval,
)
