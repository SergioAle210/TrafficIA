import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image
from scripts.figures import plot_mobility
from scripts.figures.build_collection import build_collection
from scripts.figures.export_charts import load_campaign, run_labels
from scripts.figures.plot_demand import minute_edges, proportions


class DemandPlottingTests(unittest.TestCase):
    def test_report_resolves_relocated_run_without_completed_trips(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run = root / 'registros propios' / 'mi caso'
            run.mkdir(parents=True)
            (run / 'run_config.json').write_text(json.dumps({'run_id': run.name}))
            (run / 'vehicle_history.csv').write_text('trip_id\n')
            (run / 'events_log.csv').write_text('event_type\n')
            (run / 'trips_log.csv').write_text('status,destination_id,destination_category,travel_time_s,departure_sim_time_s,selection_class\n'
                                               'aborted,A,work,2,0,routine\n')
            def distribution(value):
                return {'by_id': [{'value': 'A', 'proportion': value}], 'by_category': [{'value': 'work', 'proportion': value}]}
            metrics = dict(run=run.name, source_directory='old-location', seed=17, vehicle_count=3, scenario='history_80_20',
                           started=1, completed=0, travel_time={'mean_s': None}, integrity_errors=[],
                           destinations={'assigned': distribution(1.), 'reached': distribution(None)})
            (root / 'analysis.json').write_text(json.dumps({'runs': [metrics]}))
            campaign = load_campaign(root, runs_root=run.parent)
            self.assertEqual(campaign['trip_sources'], [run / 'trips_log.csv'])
            self.assertEqual(campaign['groups'], [(3, 17)])
            self.assertIn('semilla 17', run_labels(campaign)[0])
            self.assertIsNone(campaign['flow'])

    def test_collection_checks_figure_hash_before_publishing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'resultado.png'
            Image.new('RGB', (2, 2)).save(source)
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            item = {'name': 'resultado', 'title': 'Movilidad', 'files': [{'path': source.name, 'sha256': digest}]}
            (root / 'manifest.json').write_text(json.dumps({'figures': [item]}))
            build_collection([root], [], root / 'coleccion')
            record = json.loads((root / 'coleccion/catalogo.json').read_text())['figures'][0]['files'][0]
            self.assertEqual((root / 'coleccion' / record['path']).read_bytes(), source.read_bytes())
            source.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'exportaci'):
                build_collection([root], [], root / 'otra')
            self.assertFalse((root / 'otra').exists())

    def test_short_campaign_keeps_undefined_values_distinct_from_zero(self):
        run = {'destinations': {'reached': {'by_id': [
            {'value': 'T01_044', 'proportion': None},
        ]}}}
        self.assertTrue(np.isnan(proportions(run, 'reached', 'by_id', ['T01_044'])[0]))
        figure, axis = plot_mobility.plt.subplots()
        self.addCleanup(plot_mobility.plt.close, figure)
        plot_mobility.bars(axis, [None, 0., None, 7.35], 'Tiempo de viaje', 'Segundos', '.2f')
        self.assertEqual([label.get_text() for label in axis.texts], ['N/D', '0.00', 'N/D', '7.35'])

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
