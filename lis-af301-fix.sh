#!/bin/bash

awk -F , -v OFS=, 'NR == 1 {print "bait","target",$0} NR > 1 {bait=gensub(/([a-zA-Z0-9_]+)__([a-zA-Z0-9_]+)/,"\\1","1",$1);
    target=gensub(/([a-zA-Z0-9_]+)__([a-zA-Z0-9_]+)/,"\\2","1",$1);
    print bait,target,$0}' "$@"
