#!/bin/bash

script_path=$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")

if [[ -n "$CC_CLUSTER" ]]
then
  module purge
  module load StdEnv/2023
  module load nextflow/25.04.6
fi
export NXF_OPTS="-Xms500M -Xmx8000M"

export PATH="$script_path":$PATH
source "${script_path}/pairs-env/bin/activate"
