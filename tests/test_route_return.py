"""Same-edge goals must use a directed circuit, never reverse the lane."""
import unittest
from types import SimpleNamespace as NS
from unittest.mock import Mock
import networkx as nx
from src.route_planner import same_edge_return_path


class ReturnRouteTests(unittest.TestCase):
    def planner(self, lane=-1, start_s=80, goal_s=20):
        graph = nx.DiGraph()
        graph.add_weighted_edges_from([(1, 2, 100), (2, 3, 10), (3, 1, 10)], weight="length")
        waypoints = [NS(road_id=10, section_id=0, lane_id=lane, s=s) for s in (start_s, goal_s)]
        return NS(_graph=graph, _localize=Mock(return_value=(1, 2)),
                  _wmap=NS(get_waypoint=Mock(side_effect=waypoints)))

    def test_return_traverses_current_edge_twice_in_legal_direction(self):
        planner = self.planner()
        result = same_edge_return_path(planner, object(), object())
        self.assertEqual(result, [1, 2, 3, 1, 2])
        self.assertTrue(all(planner._graph.has_edge(a, b) for a, b in zip(result, result[1:])))

    def test_positive_lane_uses_decreasing_s_and_detects_subsample_return(self):
        for lane, start, goal in [(1, 20, 80), (-1, 20.4, 20.2)]:
            self.assertEqual(same_edge_return_path(self.planner(lane, start, goal), 0, 1), [1, 2, 3, 1, 2])

    def test_ahead_and_identical_goals_delegate_to_official_search(self):
        for lane, start, goal in [(-1, 20, 80), (1, 80, 20), (-1, 20, 20)]:
            self.assertIsNone(same_edge_return_path(self.planner(lane, start, goal), 0, 1))

    def test_other_edges_delegate_and_disconnected_return_is_rejected(self):
        planner = self.planner()
        planner._localize.side_effect = [(1, 2), (2, 3)]
        self.assertIsNone(same_edge_return_path(planner, 0, 1))
        planner = self.planner()
        planner._graph.remove_edge(3, 1)
        with self.assertRaisesRegex(RuntimeError, "circuito dirigido"):
            same_edge_return_path(planner, 0, 1)


if __name__ == "__main__":
    unittest.main()
