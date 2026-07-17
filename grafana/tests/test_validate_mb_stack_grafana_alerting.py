import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "validate-mb-stack-grafana-alerting.py"
SPEC = importlib.util.spec_from_file_location("validate_mb_stack_grafana_alerting", SCRIPT)
assert SPEC and SPEC.loader
validator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = validator
SPEC.loader.exec_module(validator)


class ValidateGrafanaAlertingTests(unittest.TestCase):
    def write_alerts(self, directory: Path, uid: str) -> None:
        (directory / "live-alert-rules.json").write_text(
            json.dumps(
                {
                    "groups": [
                        {
                            "name": "Default",
                            "rules": [{"uid": uid, "title": "Example rule"}],
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )

    def test_accepts_a_40_character_uid(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            self.write_alerts(directory, "x" * 40)

            self.assertEqual([], validator.validate_alerting_directory(directory))

    def test_rejects_a_uid_longer_than_grafana_limit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            self.write_alerts(directory, "x" * 41)

            errors = validator.validate_alerting_directory(directory)

            self.assertEqual(1, len(errors))
            self.assertIn("41 characters", errors[0])
            self.assertIn("at most 40", errors[0])


if __name__ == "__main__":
    unittest.main()
