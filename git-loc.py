#!/usr/bin/env python
import os
import csv
import sys
import json
from os.path import splitext
from collections import defaultdict
import asyncio

from rich import print
from rich.table import Table
from git import Repo, Blob
from aiofile import async_open
from tqdm import tqdm

COLS = ('lines', 'files', 'blanks', 'bytes')
totals = {'total': defaultdict(int)}  # k: defaultdict(int) for k in COLS}


async def counter(entry):
    global totals
    stem, ext = splitext(entry.path)
    ext = ext[1:] if ext else 'other'
    totals[ext]['files'] += 1
    totals[ext]['bytes'] += entry.size
    async with async_open(entry.path, 'rb') as f:
        while line := await f.readline():
            # for line in f.readlines():
            k = 'blanks' if line.isspace() else 'lines'
            totals[ext][k] += 1


async def index(repo):
    tasks = [counter(entry) for entry in repo.index.entries.values()]
    await asyncio.gather(*tasks)

    for key, counts in totals.items():
        for ext, count in counts.items():
            print(key, ext, count)
    with open('totals.json', 'w') as f:
        json.dump(totals, f, indent=2, sort_keys=True)


def tree(repo):
    global totals
    items = list(repo.tree().traverse(lambda i, d: isinstance(i, Blob), visit_once=True))
    for item in tqdm(items):
        stem, ext = splitext(item.path)
        ext = ext[1:] if ext else 'other'
        if ext not in totals:
            totals[ext] = defaultdict(int)
        totals[ext]['files'] += 1
        totals[ext]['bytes'] += item.size
        for line in item.data_stream.stream.readlines():
            k = 'blanks' if line.isspace() else 'lines'
            totals[ext][k] += 1


def main(working_dir=None):
    repo = Repo(os.getcwd() if working_dir is None else working_dir)
    tree(repo)
    for ext, counts in totals.items():
        for key, count in counts.items():
            totals['total'][key] += count
    header = ('extension',) + COLS
    table = Table(*header, title=f'Git File Line Counts\n{repo.working_dir}', show_header=True, header_style='bold magenta')
    for ext, counts in sorted(totals.items(), key=lambda x: x[1]['lines']):
        table.add_row(ext, *[str(counts[col]) for col in COLS])
    print(table)
    rows = [[ext] + [counts[col] for col in COLS] for ext, counts in totals.items()]
    # print({key: dict(value) for key, value in totals.items()})

    # asyncio.run(index(repo))
    with open('totals.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(sorted(rows, key=lambda x: x[1]))
    # from IPython import embed

    # embed(colors='linux')


if __name__ == '__main__':
    main(sys.path[-1] if len(sys.argv) > 1 else None)
