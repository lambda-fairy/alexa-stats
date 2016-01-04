#!/usr/bin/env python3


from collections import defaultdict
import html5lib
import os
from multiprocessing import Pool
from pprint import pprint


# Ensure that all file paths are relative to the script directory
os.chdir(os.path.dirname(__file__))


def load_files(dirname):
    """Yield all the files in the specified directory."""
    for name in os.listdir(dirname):
        with open(os.path.join(dirname, name), 'rb') as f:
            yield f.read()
            print('Loaded', name)


def tag_name(elem):
    """Extract the unqualified tag name from an element."""
    name = elem.tag.split('}')[-1]
    # Some nodes have weird values as the tag name; no idea why
    # This encoding operation makes sure that these weird nodes result
    # in an error
    name.encode('ascii')
    return name


def len_iter(it):
    """Return the number of elements yielded by an iterator."""
    return sum(1 for _ in it)


def undefaultdict(d):
    """
    Convert a defaultdict of defaultdicts to a dict of dicts.

    This is necessary because defaultdicts can't be serialized, a
    requirement for multiprocessing.
    """
    return {k: dict(v) for k, v in d.items()}


def summarize_page(root):
    """Given the root of a parse tree, return a nested dict mapping each
    tag type to its possible children."""
    summary = defaultdict(lambda: defaultdict(int))
    def walk(elem):
        tag = tag_name(elem)
        if elem.text and not elem.text.isspace():
            summary[tag][None] += 1
        for child in elem:
            try:
                child_tag = tag_name(child)
            except Exception:
                continue
            summary[tag][child_tag] += 1
            if child.tail and not child.tail.isspace():
                summary[tag][None] += 1
            walk(child)
    walk(root)
    return undefaultdict(summary)


def collate_summaries(summaries):
    """Given an iterable of summaries returned by ``summarize_page``,
    combine them all into a single summary."""
    ubersummary = defaultdict(lambda: defaultdict(int))
    for summary in summaries:
        for parent, children in summary.items():
            for child, count in children.items():
                ubersummary[parent][child] += count
    return undefaultdict(ubersummary)


def main():
    pool = Pool()
    # Parsing is very slow, so run lots of instances in parallel
    trees = pool.imap_unordered(html5lib.parse, load_files('alexa-pages'))
    summaries = pool.imap_unordered(summarize_page, trees)
    ubersummary = collate_summaries(summaries)
    pprint(ubersummary)


if __name__ == '__main__':
    main()
