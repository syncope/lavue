#!/bin/bash
if [[ -z $1 ]] ; then
    echo "fetches a lavue source from github.com to the dist/ directory"
    echo ""
    echo "usage:"
    echo "       fetchsource.sh  <version>"
    echo " "
    echo "e.g."
    echo "       fetchsource.sh 2.27.1"
else
    echo "fetching version: v$1"
    mkdir -p dist
    curl https://codeload.github.com/jkotan/lavue/tar.gz/v$1 > dist/lavue-$1.tar.gz
fi
