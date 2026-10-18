"""Offline command line. Output is a diagnosis, never a Power BI project."""
import argparse
import os
from pathlib import Path
import sys
import tempfile

from .engine import analyze
from .intake import InputError, ReadOptions
from .reporting import artifacts, json_text


def dump_json(path, item):
    Path(path).write_text(json_text(item), encoding='utf-8')


def write_artifacts(output, contents, sources, overwrite=False):
    out = Path(output)
    paths = [out / name for name in contents]
    # Preflight every target before creating output. samefile also catches hardlinks.
    for target in paths:
        for source in map(Path, sources):
            if target.resolve() == source.resolve() or (target.exists() and target.samefile(source)):
                raise InputError('Destino coincide com uma fonte original; escrita recusada.')
        if target.is_symlink():
            raise InputError('Destino é um link simbólico; escrita recusada.')
        if target.exists() and (not overwrite or not target.is_file()):
            raise InputError('Artefato já existe; escolha outra pasta ou use --overwrite para artefatos gerados.')
    out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.autopilot-', dir=out) as temporary:
        staged = Path(temporary)
        for name, content in contents.items():
            (staged / name).write_text(content, encoding='utf-8', newline='\n')
        # Each replacement is atomic; the set is not a database transaction.
        for name in contents:
            os.replace(staged / name, out / name)


def run(argv=None):
    parser = argparse.ArgumentParser(description='PowerBI Autopilot Data Intelligence Engine 0.2')
    sub = parser.add_subparsers(dest='command', required=True)
    command = sub.add_parser('analyze', help='Diagnóstico local, sem alterações nas fontes')
    command.add_argument('input', nargs='+', help='CSV, XLSX ou XLSM; múltiplos caminhos aceitos')
    command.add_argument('--output', default='analysis')
    command.add_argument('--sheet', help='Nome exato da aba; padrão: todas as abas')
    command.add_argument('--sep', help='Delimitador CSV de um caractere')
    command.add_argument('--encoding', help='Codificação CSV; padrão UTF-8 com fallback diagnosticado cp1252')
    command.add_argument('--header-row', type=int, default=1, help='Linha do cabeçalho, base 1')
    command.add_argument('--locale', choices=['pt-BR', 'en-US'], help='Regra explícita para números/datas')
    command.add_argument('--overwrite', action='store_true', help='Substituir artefatos gerados na saída')
    command.add_argument('--fail-on-blocker', action='store_true', help='Retornar 2 após gravar diagnóstico com BLOCKER')
    args = parser.parse_args(argv)
    try:
        report = analyze(args.input, ReadOptions(args.sheet, args.sep, args.encoding, args.header_row), args.locale)
        write_artifacts(args.output, artifacts(report), args.input, args.overwrite)
    except (InputError, OSError) as exc:
        print(f'Erro: {exc if isinstance(exc, InputError) else "falha de acesso aos arquivos locais"}', file=sys.stderr)
        return 1
    print(f'Diagnóstico criado | tabelas: {len(report["tables"])} | estado: {report["validation"]["status"]}')
    return 2 if args.fail_on_blocker and report['validation']['counts']['BLOCKER'] else 0


if __name__ == '__main__':
    sys.exit(run())
