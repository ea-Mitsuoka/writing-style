import contextlib
import io
import unittest

from src.ci import template_sync_size_exception as exception

SOURCE_LINE = (
    "Direct-parent-source: https://github.com/ea-Mitsuoka/ai-dev-foundation@"
    "057e7a404dd643d1e0b639dd1c35eecb994d2166"
)


def sync_pull_request(**overrides):
    fields = {
        "pr_author": "github-actions[bot]",
        "head_repository": "ea-Mitsuoka/writing-style",
        "target_repository": "ea-Mitsuoka/writing-style",
        "head_ref": "chore/template_sync_057e7a4",
        "base_ref": "main",
        "pr_body": f"{SOURCE_LINE}\n\nBefore merge:\n- Review the range.",
    }
    fields.update(overrides)
    return fields


class AuthenticatedTemplateSyncTest(unittest.TestCase):
    def test_bot_sync_with_exact_parent_provenance_is_authenticated(self):
        self.assertTrue(exception.is_authenticated_template_sync(**sync_pull_request()))

    def test_each_missing_condition_rejects_the_pull_request(self):
        for field, value in (
            ("pr_author", "ea-Mitsuoka"),
            ("head_repository", "someone/writing-style"),
            ("target_repository", "someone/writing-style"),
            ("head_ref", "chore/template_sync_not-a-hash"),
            ("head_ref", "feature/template_sync_057e7a4"),
            ("base_ref", "release"),
            ("pr_body", "No provenance here."),
            ("pr_body", SOURCE_LINE.replace("ai-dev-foundation", "other-parent")),
            ("pr_body", SOURCE_LINE[:-1]),
            ("pr_body", f"quoted {SOURCE_LINE}"),
        ):
            with self.subTest(field=field, value=value):
                self.assertFalse(
                    exception.is_authenticated_template_sync(**sync_pull_request(**{field: value}))
                )


class GateTest(unittest.TestCase):
    def run_gate(self, policy_status, authenticated):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = exception.gate(policy_status, authenticated_template_sync=authenticated)
        return status, output.getvalue()

    def test_authenticated_sync_downgrades_the_hard_limit_to_a_warning(self):
        status, output = self.run_gate(1, True)

        self.assertEqual(0, status)
        self.assertIn("::warning::Authenticated mechanical Template Sync", output)

    def test_other_pull_requests_keep_the_hard_limit_failure(self):
        self.assertEqual((1, ""), self.run_gate(1, False))

    def test_invalid_policy_input_is_never_downgraded(self):
        self.assertEqual((2, ""), self.run_gate(2, True))

    def test_passing_policy_stays_passing(self):
        self.assertEqual((0, ""), self.run_gate(0, False))


if __name__ == "__main__":
    unittest.main()
