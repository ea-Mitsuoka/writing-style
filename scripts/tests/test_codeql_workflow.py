import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LANGUAGE_MATRIX = re.compile(r"(?m)^\s*language:\s*\[([^\]\r\n]*)\]\s*(?:#.*)?$")
CODEQL_ACTION = re.compile(
    r"github/codeql-action/(?P<action>[^@\s]+)@"
    r"(?P<sha>[0-9a-f]{40})\s+#\s+(?P<version>v\S+)"
)
SUPPORTED_CODEQL_SHA = "5595ccaf912efad79be6eef63a5619ff05969be3"
SUPPORTED_CODEQL_VERSION = "v4.37.6"


def python_analysis_is_enabled(workflow: str) -> bool:
    match = LANGUAGE_MATRIX.search(workflow)
    if match is None:
        return False
    languages = {entry.strip() for entry in match.group(1).split(",") if entry.strip()}
    return "python" in languages


class CodeQLWorkflowTest(unittest.TestCase):
    def test_codeql_actions_use_supported_v4_digest(self) -> None:
        expected = {
            ".github/workflows/codeql.yml": {"init", "autobuild", "analyze"},
            ".github/workflows/scorecard.yml": {"upload-sarif"},
        }

        for path, expected_actions in expected.items():
            with self.subTest(path=path):
                workflow = (ROOT / path).read_text(encoding="utf-8")
                references = {
                    (match["action"], match["sha"], match["version"])
                    for match in CODEQL_ACTION.finditer(workflow)
                }
                self.assertEqual(
                    {
                        (action, SUPPORTED_CODEQL_SHA, SUPPORTED_CODEQL_VERSION)
                        for action in expected_actions
                    },
                    references,
                )

    def test_python_analysis_is_enabled(self) -> None:
        workflow = (ROOT / ".github/workflows/codeql.yml").read_text()

        self.assertTrue(python_analysis_is_enabled(workflow))

    def test_python_analysis_can_share_a_multi_language_matrix(self) -> None:
        workflow = "matrix:\n  language: [javascript-typescript, python]\n"

        self.assertTrue(python_analysis_is_enabled(workflow))

    def test_python_analysis_requires_an_exact_non_empty_entry(self) -> None:
        self.assertFalse(python_analysis_is_enabled("language: []\n"))
        self.assertFalse(python_analysis_is_enabled("language: [javascript-typescript]\n"))
        self.assertFalse(python_analysis_is_enabled("language: [python-custom]\n"))


if __name__ == "__main__":
    unittest.main()
