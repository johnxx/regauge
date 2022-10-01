#!/usr/bin/env bash

if [ -z "$1" ] ; then
  echo "Usage: $0 <target_dir>"
  exit 1
fi
target="$1"

diff -urN "$target/share" share 
diff -urN "$target/lib" lib 
things="
area.py
code.py
data.py
gauge_face.py
gauge.py
gauges
neopixel_slice.py
passy.py
sources
stream_spec.py
tcp_server.py
timeseries.py
uprofile.py"

for n in $things ; do
  diff -urN "$target/$n" "src/$n" 
done
