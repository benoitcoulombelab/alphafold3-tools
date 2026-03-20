#!/bin/bash

# Exit when any command fails
set -e

# load required modules
if [[ -n "$CC_CLUSTER" ]]
then
  module purge
  module load StdEnv/2023
  module load python/3.14.2
fi

rm -rf ./af3-tools-env
python3 -m venv ./af3-tools-env
source ./af3-tools-env/bin/activate
pip install .
rm -r build
rm -r af3-tools.egg-info
