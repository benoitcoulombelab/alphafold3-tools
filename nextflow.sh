#!/bin/bash
#SBATCH --account=def-coulomb
#SBATCH --time=7-00:00:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --mail-type=NONE
#SBATCH --output=nextflow-%A.out

# load required modules
if [[ -n "$CC_CLUSTER" ]]
then
  module purge
  module load StdEnv/2023
  module load nextflow/25.04.6
fi
if [[ "beluga" == "$CC_CLUSTER" ]]
then
  ulimit -v 40000000
fi

export NXF_OPTS="-Xms500M -Xmx8000M"

nextflow "$@"
