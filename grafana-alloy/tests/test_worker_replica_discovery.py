import unittest
from pathlib import Path

CONFIG = Path(__file__).resolve().parents[1] / "config.alloy"

class WorkerReplicaDiscoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = CONFIG.read_text(encoding="utf-8")

    def test_discovers_every_railway_worker_replica_over_ipv6(self) -> None:
        self.assertIn('discovery.dns "odds_ingestion_workers"', self.config)
        self.assertIn('type             = "AAAA"', self.config)
        self.assertIn('port             = 3005', self.config)
        self.assertIn('refresh_interval = "30s"', self.config)

    def test_worker_scrape_consumes_discovered_targets(self) -> None:
        self.assertIn(
            'targets          = discovery.dns.odds_ingestion_workers.targets',
            self.config,
        )
        self.assertNotIn(
            '__address__ = "odds-ingestion-worker.railway.internal:3005"',
            self.config,
        )

if __name__ == "__main__":
    unittest.main()
