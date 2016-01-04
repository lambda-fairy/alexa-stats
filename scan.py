#!/usr/bin/env python3


from collections import defaultdict
import html5lib
import json
import os
from multiprocessing import Pool
from pprint import pprint
import sys


VALID_TAGS = frozenset("""
a
abbr
acronym
address
applet
area
article
aside
audio
b
base
basefont
bdi
bdo
big
blockquote
body
br
button
canvas
caption
center
cite
code
col
colgroup
datalist
dd
del
details
dfn
dialog
dir
div
dl
dt
em
embed
fieldset
figcaption
figure
font
footer
form
frame
frameset
h1
h2
h3
h4
h5
h6
head
header
hr
html
i
iframe
img
input
ins
kbd
keygen
label
legend
li
link
main
map
mark
menu
menuitem
meta
meter
nav
noframes
noscript
object
ol
optgroup
option
output
p
param
pre
progress
q
rp
rt
ruby
s
samp
script
section
select
small
source
span
strike
strong
style
sub
summary
sup
table
tbody
td
textarea
tfoot
th
thead
time
title
tr
track
tt
u
ul
var
video
wbr
""".strip().split())


def tag_name(elem):
    """Extract the unqualified tag name from an element."""
    name = elem.tag.split('}')[-1]
    # Some nodes have weird values as the tag name; no idea why
    # This encoding operation makes sure that these weird nodes result
    # in an error
    name.encode('ascii')
    return name


def undefaultdict(d):
    """
    Convert a defaultdict of defaultdicts to a dict of dicts.

    This is necessary because defaultdicts can't be serialized, a
    requirement for multiprocessing.
    """
    return {k: dict(v) for k, v in d.items()}


def summarize_page(root):
    """
    Given the root of a parse tree, return a nested dict mapping each
    tag type to its possible children.

    Text nodes are represented by an empty string as the tag name.
    """
    summary = defaultdict(lambda: defaultdict(int))
    def walk(elem):
        tag = tag_name(elem)
        if elem.text and not elem.text.isspace():
            summary[tag][''] += 1
        for child in elem:
            try:
                child_tag = tag_name(child)
            except Exception:
                continue
            if child_tag not in VALID_TAGS:
                continue
            summary[tag][child_tag] += 1
            if child.tail and not child.tail.isspace():
                summary[tag][''] += 1
            walk(child)
    walk(root)
    return undefaultdict(summary)


def collate_summaries(summaries):
    """Given an iterable of summaries returned by ``summarize_page``,
    combine them all into a single summary."""
    summaries = list(summaries)
    ubersummary = defaultdict(lambda: defaultdict(int))
    for summary in summaries:
        for parent, children in summary.items():
            for child, count in children.items():
                ubersummary[parent][child] += count / len(summaries)
    return undefaultdict(ubersummary)


def main():
    inputs = [open(input_path, 'rb').read() for input_path in sys.argv[1:]]
    pool = Pool()
    # Parsing is very slow, so run lots of instances in parallel
    trees = pool.imap_unordered(html5lib.parse, inputs)
    summaries = pool.imap_unordered(summarize_page, trees)
    ubersummary = collate_summaries(summaries)
    json.dump(ubersummary, sys.stdout)


if __name__ == '__main__':
    main()
