#!/usr/bin/env python
import csv
import sys
from os.path import splitext
from collections import defaultdict

from git import Repo


async def counter(path):
    pass


def main(working_dir='.'):
    totals = defaultdict(int)
    repo = Repo(working_dir)
    for commit in repo.iter_commits():
        for fn, changes in commit.stats.files.items():
            stem, ext = splitext(fn)
            ext = ext[1:] if ext else 'other'
            count = changes['insertions'] - changes['deletions']
            if count:
                totals['total'] += count
                totals[ext] += count
    with open('totals.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerows(totals.items())
    from IPython import embed

    embed(colors='linux')


if __name__ == '__main__':
    main()
