import contextlib
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from powerbi_autopilot import cli


class CliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / 'source.csv'
        self.source.write_text('ID;Tipo;Valor;Moeda;Pago;Data Pagamento\n001;Receita;100,00;BRL;Sim;2026-01-15\n002;Despesa;-40,00;BRL;Sim;2026-01-16\n', encoding='utf-8')

    def run_cli(self, *args):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return cli.run(['analyze', str(self.source), *map(str, args)])

    def test_cli_artifacts_reproducible_original_preserved_and_no_row_values(self):
        before = self.source.read_bytes()
        for name in ('one', 'two'):
            self.assertEqual(self.run_cli('--output', self.root/name), 0)
        out = self.root/'one'
        r = json.loads((out/'analysis.json').read_text(encoding='utf-8'))
        self.assertEqual(r['schema_version'], '0.2.1')
        self.assertEqual(r['tables'][0]['profile']['rows'], 2)
        self.assertEqual(r['tables'][0]['profile']['source']['sha256'], hashlib.sha256(before).hexdigest())
        self.assertEqual(r['validation']['semantic_validation'], 'not_performed')
        self.assertTrue((out/'report.md').exists())
        self.assertTrue((out/'profile.json').exists())
        self.assertTrue((out/'plan.json').exists())
        self.assertEqual((out/'analysis.json').read_bytes(), (self.root/'two'/'analysis.json').read_bytes())
        self.assertEqual(self.source.read_bytes(), before)

    def test_strict_mode_uses_exit_two_but_delivers_diagnosis(self):
        self.source.write_text('Valor;Data\n1,234;01/02/2026\n', encoding='utf-8')
        out = self.root/'strict'
        self.assertEqual(self.run_cli('--output', out, '--fail-on-blocker'), 2)
        self.assertTrue((out/'analysis.json').exists())

    def test_no_overwrite_or_partial_output_on_existing_artifact(self):
        out = self.root/'out'
        out.mkdir()
        (out/'report.md').write_text('ORIGINAL', encoding='utf-8')
        self.assertEqual(self.run_cli('--output', out), 1)
        self.assertFalse((out/'analysis.json').exists())
        self.assertEqual((out/'report.md').read_text(encoding='utf-8'), 'ORIGINAL')

    def test_hardlink_to_input_cannot_be_overwritten_even_with_flag(self):
        out = self.root/'out'
        out.mkdir()
        (out/'analysis.json').hardlink_to(self.source)
        before = self.source.read_bytes()
        self.assertEqual(self.run_cli('--output', out, '--overwrite'), 1)
        self.assertEqual(self.source.read_bytes(), before)

    def test_multiple_inputs_and_invalid_format_do_not_leave_outputs(self):
        second = self.root/'clients.csv'
        second.write_text('Cliente_ID;Nome\n1;PRIVADO\n', encoding='utf-8')
        out = self.root/'multi'
        self.assertEqual(self.run_cli(second, '--output', out), 0)
        data = json.loads((out/'analysis.json').read_text(encoding='utf-8'))
        self.assertEqual(len(data['tables']), 2)
        self.assertNotIn('PRIVADO', (out/'analysis.json').read_text(encoding='utf-8'))
        bad = self.root/'bad.pbix'
        bad.write_bytes(b'')
        self.assertEqual(self.run_cli(bad, '--output', self.root/'bad'), 1)
        self.assertFalse((self.root/'bad').exists())


if __name__ == '__main__':
    unittest.main()
