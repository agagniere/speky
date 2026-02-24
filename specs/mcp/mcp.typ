#import "@local/speky:0.1.3": speky, table_to_comments

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
    "nonfunctional.yaml",
    "query.yaml",
    "discovery.yaml",
    "tracability.yaml",
    "test_01.yaml",
    "test_02.yaml",
    "test_03.yaml",
    "test_04.yaml",
    "test_05.yaml",
    "test_06.yaml",
    "test_07.yaml",
    "test_08.yaml",
    "test_09.yaml",
  ).map(yaml),
)
