import unittest
from src.analysis.incident_analysis import collision_episodes


class IncidentAnalysisTests(unittest.TestCase):
    def event(self, vehicle, other, time, kind='collision'):
        """Create a minimal sensor event with vehicle, other actor, time, and event type."""
        return dict(vehicle_id=vehicle, other_actor_id=other, simulation_time_s=time, event_type=kind)

    def test_opposite_sensors_share_episode_and_time_gap_splits_it(self):
        """Check that both vehicles' notifications share an episode until a sufficient time gap occurs."""
        rows=[self.event('b',1,10), self.event('a',2,10), self.event('a',2,11),
              self.event('a',2,12.1), self.event('a',2,10.2,'lane_invasion')]
        result=collision_episodes(rows, {'a':1,'b':2}, 10)
        self.assertEqual([e['raw_callbacks'] for e in result], [3,1])
        self.assertEqual(result[0]['span_s'],1)
        self.assertEqual(set(result[0]['sensor_vehicles']),{'a','b'})

    def test_distinct_pairs_and_unknown_objects_are_not_merged(self):
        """Check that different vehicle pairs and unidentified contacts are not incorrectly grouped together."""
        rows=[self.event('a',0,10),self.event('b',0,10),self.event('a',3,10)]
        result=collision_episodes(rows, {'a':1,'b':2}, 10)
        self.assertEqual(len(result),3)
        self.assertEqual(sum(e['ambiguous_other_id'] for e in result),2)

    def test_invalid_temporal_scope_is_rejected(self):
        """Check that invalid collision-episode time settings are rejected."""
        with self.assertRaises(ValueError):
            collision_episodes([self.event('a',2,9)], {'a':1}, 10)
