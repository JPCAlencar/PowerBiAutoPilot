import unittest
import pandas as pd

from powerbi_autopilot.profiler import profile
from powerbi_autopilot.recipes import make_plan
from powerbi_autopilot.layout import grid_to_pixels
from powerbi_autopilot.gantt import validate_gantt


class StarterTests(unittest.TestCase):
    def test_project_gantt_ready(self):
        df = pd.DataFrame({'Projeto':['A'], 'Atividade':['Planejar'], 'Data Início':['01/09/2026'], 'Data Fim':['10/09/2026'], 'Status':['OK']})
        p = make_plan(profile(df))
        self.assertEqual(p['selected_domain'], 'projects')
        self.assertEqual(next(x for x in p['proposed_visuals'] if x['visual']=='gantt')['status'], 'ready_for_date_validation')
        self.assertTrue(validate_gantt(df, 'Atividade', 'Data Início', 'Data Fim')['ready'])

    def test_project_gantt_block_without_start(self):
        df = pd.DataFrame({'Projeto':['A'], 'Atividade':['Tarefa'], 'Data Fim':['10/09/2026']})
        p = make_plan(profile(df))
        self.assertEqual(next(x for x in p['proposed_visuals'] if x['visual']=='gantt')['status'], 'blocked')

    def test_iso_dates(self):
        df = pd.DataFrame({'Projeto':['A'], 'Atividade':['A'], 'Data Início':['2026-09-15'], 'Data Fim':['2026-10-20']})
        p = make_plan(profile(df))
        self.assertEqual(next(x for x in p['proposed_visuals'] if x['visual']=='gantt')['status'], 'ready_for_date_validation')
        self.assertTrue(validate_gantt(df, 'Atividade','Data Início','Data Fim')['ready'])

    def test_invalid_dates(self):
        df = pd.DataFrame({'Atividade':['Tarefa'], 'Data Início':['10/09/2026'], 'Data Fim':['01/09/2026']})
        report = validate_gantt(df,'Atividade','Data Início','Data Fim')
        self.assertFalse(report['ready'])
        self.assertEqual(report['end_before_start_rows'], 1)

    def test_grid_overlap(self):
        with self.assertRaises(ValueError):
            grid_to_pixels([{'id':'a','column':1,'row':1,'span':6},{'id':'b','column':6,'row':1,'span':3}])

    def test_grid_bounds(self):
        with self.assertRaises(ValueError):
            grid_to_pixels([{'id':'a','column':12,'row':1,'span':2}])

    def test_no_artificial_dates(self):
        df = pd.DataFrame({'Projeto':['A'], 'Atividade':['Tarefa'], 'Data Fim':['2026-09-10']})
        p = profile(df)
        self.assertFalse(any('Data Início' == x['name'] for x in p['columns']))


if __name__ == '__main__':
    unittest.main()
