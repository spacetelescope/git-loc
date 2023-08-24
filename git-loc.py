#!/usr/bin/env python
import os
import csv
import json
from pathlib import Path
from collections import defaultdict
from mimetypes import guess_type

from rich import print
from rich.table import Table
from git import Repo, Blob
from tqdm import tqdm
import rich_click as click
from ruamel import yaml

BASE = Path(__file__).resolve().parent
LANGS = yaml.safe_load((BASE / 'languages.yml').open())
COLS = ('files', 'lines', 'blanks', 'bytes')
GROUPS = ('extension', 'mime-type', 'language')
FMTS = ('table', 'csv', 'json', 'yaml')
totals = {'total': defaultdict(int)}
config = {'groupby': 'language', 'rev': None, 'working-dir': os.getcwd(), 'fmt': 'table'}
_lang_cache = {}

click.rich_click.USE_MARKDOWN = True


def getlang(path):
    """
    The function `getlang` returns the programming language of a given file based on its name and
    extension, or returns 'other' if the language is not recognized.

    Args:
      path: The `path` parameter is a file `Path` object that represents the path to a file.

    Returns:
      the language of a given file path. If the file path matches any of the filenames or extensions
    specified in the LANGS dictionary, the corresponding language name is returned. If no match is
    found, 'other' is returned.
    """
    global _lang_cache

    if path.name in _lang_cache:
        return _lang_cache[path.name]
    for name, info in LANGS.items():
        if path.name in info.get('filenames', []) or path.suffix in info.get('extensions', []):
            _lang_cache[path.name] = name
            return name
    return 'other'


def group(path):
    """
    The `group` function takes a file path as input and returns a grouping value based on the
    configuration settings.

    Args:
      path: The `path` parameter is a string that represents the file path of the file that needs to be
    grouped.

    Returns:
      The function `group` returns a grouping value based on the configuration settings. The specific
    value returned depends on the value of the `groupby` key in the `config` dictionary. If `groupby` is
    set to 'extension', the function returns the file extension of the given path (excluding the dot) if
    it has one, otherwise it returns 'other'. If `groupby` is
    """
    global config

    path = Path(path)
    if config['groupby'] == 'extension':
        return path.suffix[1:] if path.suffix else 'other'
    elif config['groupby'] == 'mime-type':
        mimetype = guess_type(path)
        return mimetype[0] if mimetype[0] else Blob.DEFAULT_MIME_TYPE
    elif config['groupby'] == 'language':
        return getlang(path)


def tree(repo):
    """
    The `tree` function iterates through the items in a repository's tree, analyzes the git blobs
    and accumulates the counts by group and totals.
    """
    global totals

    # Just traverse the unique set of Blobs for a given tree
    items = list(repo.tree(config['rev']).traverse(lambda i, d: isinstance(i, Blob), visit_once=True))
    for item in tqdm(items):
        ext = group(item.path)
        totals.setdefault(ext, defaultdict(int))
        totals[ext]['files'] += 1
        totals['total']['files'] += 1
        totals[ext]['bytes'] += item.size
        totals['total']['bytes'] += item.size
        # Read raw blob data from the index
        for line in item.data_stream.stream.readlines():
            k = 'blanks' if line.isspace() else 'lines'
            totals[ext][k] += 1
            totals['total'][k] += 1


def fmtint(value):
    return f'{value:,}'


def fmttotals(repo):
    global config, totals

    wdir = Path(repo.working_dir)
    fmt = config['fmt']

    if fmt == 'table':
        header = (config['groupby'],) + COLS
        table = Table(*header, title=f'File Line Counts\n{wdir}', show_header=True, header_style='bold magenta')
        for ext, counts in sorted(totals.items(), key=lambda x: x[1]['lines']):
            table.add_row(ext, *[fmtint(counts[col]) for col in COLS])
        print(table)
        return
    outfile = wdir / f'git-line-totals.{fmt}'
    if fmt == 'csv':
        header = (config['groupby'],) + COLS
        rows = [[ext] + [counts[col] for col in COLS] for ext, counts in totals.items()]
        with outfile.open('w') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(sorted(rows, key=lambda x: x[1]))
    elif fmt == 'json':
        with outfile.open('w') as f:
            json.dump(totals, f, indent=2, sort_keys=True)
    elif fmt == 'yaml':
        with outfile.open('w') as f:
            yaml.dump({key: dict(counts) for key, counts in totals.items()}, f, default_flow_style=False)
    print(f'Wrote report to {outfile}')


@click.command()
@click.argument('working-dir', type=str, default=config['working-dir'])
@click.option(
    '-r', '--rev', type=str, default=config['rev'], help='Treeish (branch, tag, or commit sha) to traverse. Defaults to current HEAD'
)
@click.option(
    '-g', '--groupby', default=config['groupby'], type=click.Choice(GROUPS), help='Group results by language, mime type or file extension'
)
@click.option('-f', '--format', 'fmt', default=config['fmt'], type=click.Choice(FMTS))
def cli(working_dir, rev, groupby, fmt):
    """
    Generate Git Lines of Code counts for all files in a Git repository.

    This command inspects the git index only and doesnt need any files to be checked out.
    It counts

    - Number of files
    - Number of lines
    - Number of blank lines
    - Number of total bytes

    First argument is the `working-dir` which is the directory to traverse. Must be a git repository.

    `rev` option is the treeish (branch, tag, or commit sha) to traverse. Defaults to current HEAD.

    `groupby` option is how to group the results. the mime type to group results by. Defaults to language which is taken the list of available languages for GitHub

    `format` option is how to format the output. Defaults to `table` which prints the results in a table. Also supports csv, json or yaml

    Example:

    `$ git-loc.py /path/to/repo -r master -f yaml`
    """
    global config

    config.update({'working-dir': working_dir, 'rev': rev, 'groupby': groupby, 'fmt': fmt})
    repo = Repo(working_dir)
    tree(repo)
    fmttotals(repo)


if __name__ == '__main__':
    cli()
