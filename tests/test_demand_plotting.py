import unittest
import numpy as np
from scripts.plot_demand_campaign import minute_edges


class DemandPlottingTests(unittest.TestCase):
    def test_hour_preserves_minute_resolution_and_boundary_events(self):
        """Check that hour-long runs retain minute bins and correctly count boundary events."""
        edges = minute_edges(3600)
        self.assertEqual(len(edges), 61)
        self.assertTrue(np.all(np.diff(edges) == 60))
        counts, _ = np.histogram([0, 59.99, 60, 1799.99, 1800, 3599.99, 3600], edges)
        self.assertEqual(counts[:30].sum(), 4)
        self.assertEqual(counts[30:].sum(), 3)
        self.assertEqual(counts[-1], 2)

    def test_partial_final_window_and_invalid_duration(self):
        """Check partial final time windows and rejection of invalid durations."""
        self.assertEqual(minute_edges(125).tolist(), [0, 60, 120, 125])
        self.assertEqual(minute_edges(15).tolist(), [0, 15])
        for value in (0, -1, float('nan'), float('inf')):
            with self.assertRaises(ValueError):
                minute_edges(value)
