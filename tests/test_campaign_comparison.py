import copy
import unittest
from scripts.campaign_comparison import comparison_rows


class CampaignComparisonTests(unittest.TestCase):
    def sample(self, n):
        event=dict(observed_callbacks=0,per_vehicle_km=0)
        return dict(vehicle_count=n,scenario='random_baseline',seed=210,map='Town01',
            simulation_duration_s=3600,metrics_semantics_version=3,comparability={'weather':'rain'},
            exposure=dict(scope='fleet',distance_m=10000),integrity_errors=[],completed=10,
            speed={'mean_kmh':10},travel_time={'mean_s':100},statuses={'completed':10},
            events={'collision':dict(event),'lane_invasion':dict(event)})

    def test_matches_cases_instead_of_position_and_handles_zero_baseline(self):
        a,b=self.sample(20),self.sample(100)
        repeat=copy.deepcopy(b);repeat['completed']=12;repeat['events']['collision']['observed_callbacks']=3
        rows,_=comparison_rows([a,b],[repeat,a])
        arrival=next(r for r in rows if r['vehicle_count']==100 and r['metric']=='completed')
        self.assertEqual(arrival['delta'],2)
        self.assertEqual(arrival['relative_change_percent'],20)
        collision=next(r for r in rows if r['vehicle_count']==100 and r['metric']=='collisions')
        self.assertEqual(collision['delta'],3)
        self.assertIsNone(collision['relative_change_percent'])

    def test_rejects_changed_conditions_missing_and_duplicate_cases(self):
        a=self.sample(20);b=copy.deepcopy(a);b['comparability']['weather']='clear'
        with self.assertRaises(ValueError):comparison_rows([a],[b])
        with self.assertRaises(ValueError):comparison_rows([a],[])
        with self.assertRaises(ValueError):comparison_rows([a,a],[a])

    def test_rejects_incompatible_duration_and_integrity(self):
        a=self.sample(20)
        for field,value in [('simulation_duration_s',1800),('integrity_errors',['bad history'])]:
            b=copy.deepcopy(a);b[field]=value
            with self.assertRaises(ValueError):comparison_rows([a],[b])
