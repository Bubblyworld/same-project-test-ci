from pathlib import Path


def find_same_config(path=".", recurse=False):
    """
    Finds the first SAME config file lexicographically from the given path,
    or None if no such config file can be found.
    """
    return _find(path, "**/same.yaml" if recurse else "same.yaml")


def find_notebook(path=".", recurse=False):
    """
    Finds the first Jupyter notebook lexicographically from the given path,
    or None if no such file can be found.
    """
    return _find(path, "**/*.ipynb" if recurse else "*.ipynb")


def _find(path, globstr):
    candidates = sorted(Path(path).glob(globstr))
    if len(candidates) == 0:
        return None

    return candidates[0]
