#!/usr/bin/env python3

import argparse
import os
import re
import csv
import sys

def find_fastq_pairs(fastq_dir):
    """
    Walk through fastq_dir, find files with extensions .fastq, .fq, .fq.gz, .fastq.gz,
    parse out the prefix up to the last _[12] marker, and group into pairs.
    Returns a dict mapping prefix -> { '1': filepath, '2': filepath }.
    """
    pattern = re.compile(
        r'^(?P<prefix>.+?)_'            # everything up to the last _[12] as group 'prefix'
        r'(?P<read>[R]?)(?P<which>[12])' # R1 or 1  → which = '1', R2 or 2 → which = '2'
        r'(?:_[^/]*)?'                  # optionally more (_001, _L1, etc.)
        r'\.(?:fastq|fq)(?:\.gz)?$'     # extension
    , re.IGNORECASE)

    pairs = {}
    for root, _, files in os.walk(fastq_dir):
        for fn in files:
            m = pattern.match(fn)
            if not m:
                continue
            prefix = m.group('prefix')
            which = m.group('which')
            path = os.path.join(root, fn)
            pairs.setdefault(prefix, {})[which] = path

    # filter to only those with both mates
    complete = {p:aces for p,aces in pairs.items() if '1' in aces and '2' in aces}
    missing = set(pairs) - set(complete)
    if missing:
        sys.stderr.write(f"Warning: found {len(missing)} prefix(es) without full pairs, skipping: {', '.join(sorted(missing))}\n")
    return complete

def write_samplesheet(pairs, strandedness, out_file='samplesheet.csv'):
    """
    Write CSV with header sample,fastq_1,fastq_2,strandedness
    where sample = prefix up to first underscore.
    """
    with open(out_file, 'w', newline='') as csvf:
        w = csv.writer(csvf)
        w.writerow(['sample','fastq_1','fastq_2','strandedness'])
        for prefix in sorted(pairs):
            sample = prefix.split('_',1)[0]
            fq1 = pairs[prefix]['1']
            fq2 = pairs[prefix]['2']
            w.writerow([sample, fq1, fq2, strandedness])
    print(f"Wrote {out_file} with {len(pairs)} entries.")

def main():
    parser = argparse.ArgumentParser(
        description="Generate a samplesheet.csv from a directory of paired-end FASTQ files."
    )
    parser.add_argument('-f', '--fastq-folder',
                        required=True,
                        help="Path to folder containing FASTQ files (will scan recursively).")
    parser.add_argument('-s', '--strandedness',
                        default='auto',
                        help="Value to put in the strandedness column (default: auto).")
    args = parser.parse_args()

    fastq_dir = os.path.abspath(args.fastq_folder)
    if not os.path.isdir(fastq_dir):
        sys.exit(f"Error: {fastq_dir} is not a directory")

    pairs = find_fastq_pairs(fastq_dir)
    if not pairs:
        sys.exit("Error: No paired FASTQ files found.")
    write_samplesheet(pairs, args.strandedness)

if __name__ == '__main__':
    main()