#!/usr/bin/env bash

if [ -z "$1" ] ; then
  echo "Usage: $0 <target_dir>"
  exit 1
fi
target="$1"

cp -r share lib "$target/"
cp -r src/* "$target/"
