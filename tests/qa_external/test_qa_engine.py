"""Independent end-to-end QA probes for the V0.2 engine and its artifacts."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import powerbi_autopilot
from powerbi_autopilot.engine import analyze
from powerbi_autopilot.intake import InputError
from powerbi_autopilot.reporting import artifacts, json_text

ROOT = Path(powerbi_autopilot.__file__).resolve().parent.parent
MARKER = 'SEGREDO_NAO_DEVE_VAZAR_9F2'


class EngineCase(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix='qa-engine-'))
        self.addCleanup(shutil.rmtree, self.dir, True)

    def csv(self, name, text):
        path = self.dir / name
        path.write_text(text, encoding='utf-8', newline='')
        return path


class ArtifactTests(EngineCase):
    def test_no_cell_value_reaches_any_artifact(self):
        path = self.csv('privado.csv',
                        'Valor;Tipo;Moeda;Status;Data Pagamento;Observação\n'
                        f'100,00;Receita;BRL;Pago;2026-01-05;{MARKER}\n')
        report = analyze([path], locale='pt-BR')
        for name, content in artifacts(report).items():
            with self.subTest(artifact=name):
                self.assertNotIn(MARKER, content)
        self.assertEqual(json_text(report).count(MARKER), 0)

    def test_artifacts_are_complete_json_and_markdown(self):
        path = self.csv('ok.csv', 'Valor;Tipo;Moeda;Status;Data Pagamento\n'
                                  '100,00;Receita;BRL;Pago;2026-01-05\n')
        report = analyze([path], locale='pt-BR')
        contents = artifacts(report)
        self.assertEqual(sorted(contents), ['analysis.json', 'plan.json', 'profile.json', 'report.md'])
        for name in ('analysis.json', 'plan.json', 'profile.json'):
            with self.subTest(artifact=name):
                self.assertIn('schema_version', json.loads(contents[name]))
        self.assertIn('Semântica de negócio: **não validada**', contents['report.md'])
        plans = json.loads(contents['plan.json'])
        self.assertFalse(plans['executed'])
        self.assertTrue(all(op['executed'] is False for t in plans['tables'] for op in t['transformations']))

    def test_analysis_is_deterministic(self):
        path = self.csv('det.csv', 'Valor;Tipo;Moeda;Status;Data Pagamento\n'
                                   '100,00;Receita;BRL;Pago;2026-01-05\n'
                                   '50,00;Despesa;BRL;Pendente;2026-01-06\n')
        self.assertEqual(json_text(analyze([path], locale='pt-BR')),
                         json_text(analyze([path], locale='pt-BR')))

    def test_duplicate_rows_are_flagged_and_never_removed(self):
        path = self.csv('dups.csv', 'Valor;Tipo;Moeda\n'
                                    '10,00;Receita;BRL\n'
                                    '10,00;Receita;BRL\n')
        report = analyze([path], locale='pt-BR')
        profile = report['tables'][0]['profile']
        self.assertEqual(profile['rows'], 2)
        self.assertEqual(profile['duplicate_rows'], 1)
        # Identical rows may be legitimate: they are reported, never dropped.
        found = {(i['code'], i['severity']) for i in report['issues']}
        self.assertIn(('suspected_duplicates', 'WARNING'), found)

    def test_source_integrity_is_recorded(self):
        path = self.csv('int.csv', 'ID;Valor\n1;10,00\n')
        report = analyze([path])
        entry = report['source_integrity'][0]
        self.assertEqual(entry['file'], 'int.csv')
        self.assertEqual(len(entry['sha256']), 64)
        self.assertTrue(entry['unchanged'])
        self.assertEqual(report['stages'], {'Raw': 'preserved', 'Clean': 'planned_only',
                                            'Analytical': 'not_implemented'})
        self.assertFalse(any(i['code'] == 'source_changed_during_analysis' for i in report['issues']))

    def test_issue_contract_shape_and_row_evidence_cap(self):
        rows = ''.join(f'linha{index}\n' for index in range(1, 26))
        path = self.csv('bloqueado.csv', 'Valor\n' + rows)
        report = analyze([path])
        event = next(i for i in report['issues'] if i['code'] == 'invalid_number')
        self.assertEqual(event['severity'], 'BLOCKER')
        self.assertEqual(event['count'], 25)
        self.assertEqual(len(event['source_rows']), 20)
        self.assertTrue(event['rows_truncated'])
        self.assertEqual(event['evidence_kind'], 'observed')
        for issue in report['issues']:
            with self.subTest(code=issue['code']):
                self.assertIn(issue['severity'], {'BLOCKER', 'WARNING', 'INFO'})
                self.assertLessEqual(len(issue['source_rows']), 20)
                self.assertEqual(issue['rows_truncated'], issue['count'] > 20)
                self.assertTrue(issue['scope'])
        self.assertEqual(report['validation']['status'], 'blocked_scopes')
        self.assertIn('monetary_metrics', report['validation']['blocked_scopes'])
        self.assertEqual(report['validation']['semantic_validation'], 'not_performed')


class DiagnosisRuleTests(EngineCase):
    def test_schedule_blocker_requires_start_and_end(self):
        path = self.csv('tarefas.csv', 'Tarefa;Responsável;Status\nA;Ana;Concluído\n')
        report = analyze([path])
        event = next(i for i in report['issues'] if i['code'] == 'insufficient_schedule_dates')
        self.assertEqual(event['severity'], 'BLOCKER')
        self.assertEqual(event['scope'], 'project_schedule')
        self.assertEqual(event['count'], 1)

    def test_schedule_with_both_dates_does_not_raise_the_schedule_blocker(self):
        path = self.csv('crono.csv',
                        'Atividade;Data Início;Data Fim\nA;2026-01-01;2026-01-05\n')
        report = analyze([path])
        self.assertFalse(any(i['code'] == 'insufficient_schedule_dates' for i in report['issues']))
        roles = {s['role'] for c in report['tables'][0]['semantics'] for s in c['suggestions']}
        self.assertTrue({'task', 'start_date', 'end_date'} <= roles)

    def test_identical_sources_are_rejected_once(self):
        first = self.csv('a.csv', 'ID;Valor\n1;10,00\n')
        second = self.dir / 'b.csv'
        shutil.copyfile(first, second)
        with self.assertRaises(InputError) as ctx:
            analyze([first, second])
        self.assertIn('Fonte/aba repetida', str(ctx.exception))

    def test_join_risk_and_orphans_are_promoted_to_findings(self):
        left = self.csv('vendas.csv', 'Cliente_ID;Valor\n1;10,00\n1;20,00\n9;30,00\n')
        right = self.csv('clientes.csv', 'Cliente_ID\n1\n1\n')
        report = analyze([left, right])
        found = {(i['code'], i['severity']) for i in report['issues']}
        self.assertIn(('join_multiplication_risk', 'BLOCKER'), found)
        self.assertIn(('candidate_orphans', 'WARNING'), found)
        scopes = {i['scope'] for i in report['issues'] if i['code'] == 'join_multiplication_risk'}
        self.assertTrue(any('join:' in scope for scope in scopes))
        self.assertTrue(all(c['validated'] is False for c in report['relationships']['candidates']))


class CliTests(EngineCase):
    def run_cli(self, *args):
        env = dict(os.environ, PYTHONIOENCODING='utf-8')
        return subprocess.run([sys.executable, '-m', 'powerbi_autopilot.cli', 'analyze', *args],
                              cwd=str(ROOT), capture_output=True, text=True, env=env,
                              encoding='utf-8', errors='replace')

    def test_exit_zero_and_artifacts_written(self):
        path = self.csv('limpo.csv', 'Valor;Tipo;Moeda;Status;Data Pagamento\n'
                                     '100,00;Receita;BRL;Pago;2026-01-05\n')
        out = self.dir / 'out'
        done = self.run_cli(str(path), '--output', str(out), '--locale', 'pt-BR')
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn('tabelas: 1', done.stdout)
        for name in ('analysis.json', 'profile.json', 'plan.json', 'report.md'):
            self.assertTrue((out / name).is_file(), name)
        again = self.run_cli(str(path), '--output', str(out), '--locale', 'pt-BR')
        self.assertEqual(again.returncode, 1)
        self.assertIn('Artefato já existe', again.stderr)

    def test_fail_on_blocker_returns_two(self):
        path = self.csv('sem_moeda.csv', 'ID;Valor\n1;10,00\n')
        out = self.dir / 'blocked'
        clean = self.run_cli(str(path), '--output', str(out))
        self.assertEqual(clean.returncode, 0, clean.stderr)
        strict = self.run_cli(str(path), '--output', str(out), '--overwrite', '--fail-on-blocker')
        self.assertEqual(strict.returncode, 2, strict.stderr)

    def test_missing_input_returns_one_without_traceback(self):
        done = self.run_cli(str(self.dir / 'ausente.csv'), '--output', str(self.dir / 'x'))
        self.assertEqual(done.returncode, 1)
        self.assertIn('Erro:', done.stderr)
        self.assertNotIn('Traceback', done.stderr)


if __name__ == '__main__':
    unittest.main()

