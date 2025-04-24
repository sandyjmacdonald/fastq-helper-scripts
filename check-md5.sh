#!/usr/bin/env bash
set -euo pipefail

# Check args
if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <directory>"
  exit 1
fi

dir="$1"
if [[ ! -d "$dir" ]]; then
  echo "Error: '$dir' is not a directory."
  exit 1
fi

failures=0

# Enable nullglob so that *.md5 with no matches expands to nothing
shopt -s nullglob

for file in "$dir"/*; do
  # skip anything that isn't a regular file or is already a .md5
  [[ -f "$file" ]] || continue
  [[ "$file" == *.md5 ]] && continue

  md5file="${file}.md5"
  if [[ ! -f "$md5file" ]]; then
    echo "Warning: no checksum file for '$file'"
    continue
  fi

  # extract the expected checksum (first field of the .md5 file)
  expected=$(cut -d ' ' -f1 < "$md5file")
  # compute the actual checksum
  actual=$(md5sum "$file" | awk '{print $1}')

  if [[ "$expected" == "$actual" ]]; then
    echo "OK:       $(basename "$file")"
  else
    echo "FAILED:   $(basename "$file")"
    echo "  expected: $expected"
    echo "       got: $actual"
    ((failures++))
  fi
done

if (( failures > 0 )); then
  echo
  echo "$failures file(s) failed checksum."
  exit 1
else
  echo
  echo "All checksums match."
  exit 0
fi