#import "@local/speky:0.3.0": speky
#speky(
  (
    "simple_requirements.yaml",
    "simple_tests.yaml",
    "simple_comments.yaml",
    "more_tests.yaml",
    "more_comments.yaml",
  ).map(yaml)
    + (
      "more_requirements.toml",
    ).map(toml),
)
