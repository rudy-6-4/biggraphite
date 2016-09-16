#!/bin/sh

PG_DIR=$(dirname $(dirname $0))
RAW_README_URL=https://raw.github.com/criteo/biggraphite/master/README.md
GITHUB_API_URL=https://api.github.com/markdown/raw

cat $PG_DIR/header.inc
curl -s -L $RAW_README_URL | curl -s --data-binary @- -H 'Content-Type: text/plain' $GITHUB_API_URL
cat $PG_DIR/footer.inc
