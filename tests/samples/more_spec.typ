#import "@local/speky:0.1.3": speky
#speky(
  (
    "simple_requirements.yaml",
    "simple_tests.yaml",
    "simple_comments.yaml",
    "more_requirements.yaml",
    "more_tests.yaml",
    "more_comments.yaml",
  ).map(yaml),
)
