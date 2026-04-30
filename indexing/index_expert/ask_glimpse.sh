#!/bin/bash

# A thin wrapper around index_expert:main which adds some recommended flags.
#
# Example usage:
# ask_glimpse.sh --bundle_names=my_bundle

# Fail on any error.
set -e

source gbash.sh || exit

GBASH_PASSTHROUGH_UNKNOWN_FLAGS=1
gbash::init_google "$@"

# Go to google3 directory.
ORIGINAL_DIR=$(pwd)
trap "cd $ORIGINAL_DIR" EXIT SIGINT
GOOGLE3=$(gbash::get_google3_dir) || exit
cd "$GOOGLE3"

blaze build //coresystems/data/excellence/applications/indexing/index_expert:main
./blaze-bin/coresystems/data/excellence/applications/indexing/index_expert/main \
  "${GBASH_ARGV[@]}"
