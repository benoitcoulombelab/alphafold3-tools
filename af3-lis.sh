#!/bin/bash
#SBATCH --account=def-coulomb
#SBATCH --time=1-00:00:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --output=af3-lis-%A.out

# Exit when any command fails
set -e

script_path=$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")
if ! [[ -f "${script_path}/af3-lis.sh" ]] && [[ -n "$SLURM_JOB_ID" ]]
then
  script_path=$(dirname "$(scontrol show job "$SLURM_JOB_ID" | awk -F '=' '$0 ~ /Command=/ {print $2; exit}')")
fi

source "${script_path}/af3-tools-env/bin/activate"

echo "Running af3-lis with parameters $*"
af3-lis "$@"
