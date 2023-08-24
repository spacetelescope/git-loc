# Git Line Counts

Generate Git Lines of Code counts for all files in a Git repository.

This command inspects the git index only and doesnt need any files to be checked
out. It counts

- Number of files
- Number of lines
- Number of blank lines
- Number of total bytes

## Install

```bash
git clone git@github.com:spacetelescope/git-loc.git
python -m pip install -r requirements.txt
```

## Running

Usage: git-loc.py [OPTIONS] [WORKING_DIR]

First argument is the `working-dir` which is the directory to traverse. Must be
a git repository.

`rev` option is the treeish (branch, tag, or commit sha) to traverse. Defaults
to current HEAD.

`groupby` option is how to group the results. the mime type to group results by.
Defaults to language which is taken the list of available languages for GitHub

`format` option is how to format the output. Defaults to `table` which prints
the results in a table. Also supports csv, json or yaml

Example:

`$ git-loc.py /path/to/repo -r main -f yaml`
