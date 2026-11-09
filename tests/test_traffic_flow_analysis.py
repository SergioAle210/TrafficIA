import unittest
from src.analysis.traffic_flow_analysis import split_space_time_interval, edie_metrics, density_band_guides


class TrafficFlowAnalysisTests(unittest.TestCase):
    def test_constant_speed_and_identity(self):
        k,q,v=edie_metrics(10,50,50,60)
        self.assertAlmostEqual(k,10/3)
        self.assertAlmostEqual(q,60)
        self.assertAlmostEqual(v,18)
        self.assertAlmostEqual(q,k*v)

    def test_stopped_vehicle_and_empty_cell(self):
        self.assertEqual(edie_metrics(60,0,50,60),(20,0,0))
        self.assertEqual(edie_metrics(0,0,50,60),(0,0,None))

    def test_spatial_and_temporal_boundary_conservation(self):
        parts=split_space_time_interval(40,60,59,61,100)
        self.assertEqual(parts,[(0,0,1,10),(1,1,1,10)])
        self.assertEqual(sum(p[2] for p in parts),2)
        self.assertEqual(sum(p[3] for p in parts),20)

    def test_reverse_direction_and_clipped_tail(self):
        parts=split_space_time_interval(65,45,0,2,70)
        self.assertEqual(parts,[(0,0,.5,5)])

    def test_stationary_on_boundary_has_one_owner(self):
        self.assertEqual(split_space_time_interval(50,50,0,1,100),[(1,0,1,0)])

    def test_partial_time_window_uses_actual_duration(self):
        self.assertEqual(edie_metrics(30,150,50,30),(20,360,18))

    def test_invalid_time_and_impossible_exposure_rejected(self):
        with self.assertRaises(ValueError):split_space_time_interval(0,1,2,1,100)
        with self.assertRaises(ValueError):edie_metrics(0,1,50,60)

    def test_guides_pool_exposure_instead_of_averaging_speeds(self):
        cells=[dict(vehicle_seconds=15,duration_s=60,longitudinal_distance_m=100),
               dict(vehicle_seconds=5,duration_s=30,longitudinal_distance_m=0)]
        row=density_band_guides(cells,min_cells=2)[0]
        self.assertAlmostEqual(row['density_veh_per_km_lane'],1000*20/4500)
        self.assertAlmostEqual(row['flow_veh_per_h_lane'],3600*100/4500)
        self.assertEqual(row['speed_kmh'],18)
        self.assertAlmostEqual(row['flow_veh_per_h_lane'],row['density_veh_per_km_lane']*row['speed_kmh'])
        self.assertTrue(row['supported'])

    def test_sparse_or_absent_bands_break_guides_without_dropping_raw_cells(self):
        def cell(k):return dict(vehicle_seconds=k*3,duration_s=60,longitudinal_distance_m=0)
        rows=density_band_guides([cell(5),cell(5),cell(15),cell(25),cell(25),cell(45),cell(45)],min_cells=2)
        self.assertEqual([r['cells'] for r in rows],[2,1,2,2])
        self.assertEqual([r['segment'] for r in rows],[0,None,1,2])
        self.assertEqual([r['band'] for r in rows],[0,1,2,4])

    def test_guide_boundaries_empty_cells_and_stopped_presence(self):
        rows=density_band_guides([dict(vehicle_seconds=0,duration_s=60,longitudinal_distance_m=0),
                                dict(vehicle_seconds=30,duration_s=60,longitudinal_distance_m=0)],min_cells=1)
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['band'],1)
        self.assertEqual(rows[0]['speed_kmh'],0)
        self.assertEqual(rows[0]['cells'],1)

    def test_guide_invalid_parameters_and_nonfinite_data_are_rejected(self):
        with self.assertRaises(ValueError):density_band_guides([],width=0)
        with self.assertRaises(ValueError):density_band_guides([],min_cells=0)
        with self.assertRaises(ValueError):density_band_guides([dict(vehicle_seconds=float('nan'),duration_s=60,longitudinal_distance_m=0)])


if __name__=='__main__':unittest.main()
