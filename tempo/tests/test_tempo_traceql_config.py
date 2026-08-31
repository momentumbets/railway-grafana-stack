import unittest
from pathlib import Path

CONFIG = Path(__file__).resolve().parents[1] / "tempo.yml"

class TempoTraceqlConfigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = CONFIG.read_text(encoding="utf-8")

    def test_enables_local_blocks_for_traceql_metrics(self) -> None:
        self.assertIn('processors: ["span-metrics", "service-graphs", "local-blocks"]', self.config)
        self.assertIn("    local_blocks:\n", self.config)

    def test_uses_tempo_2_7_compatible_bounded_configuration(self) -> None:
        self.assertIn("      max_live_traces: 20000", self.config)
        self.assertNotIn("max_live_traces_bytes", self.config)
        self.assertIn("      max_block_bytes: 50000000", self.config)
        self.assertIn("      complete_block_timeout: 20m", self.config)
        self.assertIn("      flush_to_storage: true", self.config)
        self.assertIn("  traces_storage:\n    path: /var/tempo/generator/traces", self.config)

    def test_live_generator_window_fits_inside_local_block_retention(self) -> None:
        self.assertIn(
            "query_frontend:\n  metrics:\n    query_backend_after: 15m",
            self.config,
        )
        self.assertIn("    max_duration: 3h", self.config)
        self.assertIn("      complete_block_timeout: 20m", self.config)

if __name__ == "__main__":
    unittest.main()
