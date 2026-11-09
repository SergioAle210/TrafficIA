"""Pilot invariants: nested fleets, complete histories, stable personal RNGs."""
import json
import unittest
from pathlib import Path

from scripts.prepare_pilots import nested_spawns
from src.demand.destinations import load_destinations
from src.simulation.trip_runner import TripSimulation, TripSimulationConfig
from src.demand.vehicle_history import VehicleHistory

ROOT = Path(__file__).resolve().parents[1]


class PilotPreparationTests(unittest.TestCase):
    def test_nested_spawn_extension_uses_distance_and_deterministic_ties(self):
        points = {0:(0,0), 1:(10,0), 2:(-10,0), 3:(2,0)}
        self.assertEqual(nested_spawns(points,[0],4), [0,1,2,3])
        with self.assertRaises(ValueError): nested_spawns(points,[0,0],3)
        with self.assertRaises(ValueError): nested_spawns(points,[0],5)

    def test_prepared_fleets_preserve_spawns_histories_and_individual_random_streams(self):
        destinations = load_destinations(ROOT/'data/input/Town01/destinations_config.csv','Town01')
        allowed = {d.destination_id for d in destinations}
        previous_spawns = [133,6,101]
        previous_histories, previous_choices = {}, {}
        for count in (5,10,20):
            config = TripSimulationConfig.from_json(ROOT/('config/pilots/town01_%02d.json' % count))
            self.assertEqual(config.vehicle_count,count)
            self.assertFalse(config.initial_spawn_fallback_enabled)
            self.assertEqual(config.resolved_spawn_point_indices()[:len(previous_spawns)],previous_spawns)
            simulation = TripSimulation(config,ROOT,1)
            simulation.destinations = destinations
            simulation.destinations_by_id = {d.destination_id:d for d in destinations}
            simulation._load_vehicle_histories()
            current, choices = {}, {}
            for state in simulation.vehicle_states:
                history = state.vehicle_history
                self.assertEqual(len(history.events),30)
                self.assertEqual([e.sequence for e in history.events],list(range(1,31)))
                self.assertEqual({simulation.destinations_by_id[e.destination_id].category for e in history.events},
                                 {'residential','work_education','services_leisure'})
                current[state.vehicle_id] = history.events
                choices[state.vehicle_id] = [simulation._select_next_destination(state).destination.destination_id for _ in range(12)]
                if state.vehicle_id in previous_histories:
                    self.assertEqual(current[state.vehicle_id],previous_histories[state.vehicle_id])
                    self.assertEqual(choices[state.vehicle_id],previous_choices[state.vehicle_id])
                if int(state.vehicle_id[-3:])<=5:
                    original = VehicleHistory.from_csv(ROOT/'data/input/Town01/vehicle_history_dummy.csv',state.vehicle_id,allowed)
                    self.assertEqual(history.events,original.events)
            previous_spawns, previous_histories, previous_choices = config.resolved_spawn_point_indices(), current, choices


if __name__=='__main__': unittest.main()
