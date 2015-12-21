#!/usr/bin/env python3


from collections import defaultdict
import html5lib
import os
from multiprocessing import Pool
from pprint import pprint


os.chdir(os.path.dirname(__file__))


def load_files():
    dirname = 'alexa-pages'
    for name in os.listdir(dirname):
        print(name)
        with open(os.path.join(dirname, name), 'rb') as f:
            yield f.read()


def tag_name(elem):
    """Extract the unqualified tag name from an element."""
    name = elem.tag.split('}')[-1]
    name.encode('ascii')
    return name


def len_iter(it):
    """Return the number of elements yielded by an iterator."""
    return sum(1 for _ in it)


def undefaultdict(d):
    return {k: dict(v) for k, v in d.items()}


def summarize(root):
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


def ubersummarize(summaries):
    ubersummary = defaultdict(lambda: defaultdict(int))
    for summary in summaries:
        for parent, children in summary.items():
            for child, count in children.items():
                ubersummary[parent][child] += count
    return undefaultdict(ubersummary)


def main():
    pool = Pool()
    trees = pool.imap_unordered(html5lib.parse, load_files())
    summaries = pool.imap_unordered(summarize, trees)
    ubersummary = ubersummarize(summaries)
    pprint(ubersummary)


if __name__ == '__main__':
    main()
