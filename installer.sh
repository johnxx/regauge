#!/usr/bin/env bash

if [ -z "$1" ] ; then
  echo "Usage: $0 <target_dir>"
  exit 1
fi
target="$1"

mkdir -p "$target"
if ! [ -d "$target" ] ; then
  exit 2
fi

cp -r fonts lib "$target/"
cp -r src/* "$target/"
mkdir -p "$target/config.d"
cp -r defaults/ "$target/config.d"
