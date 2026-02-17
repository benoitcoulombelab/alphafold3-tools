#!/bin/bash
#SBATCH --account=def-coulomb
#SBATCH --time=1-00:00:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=30G
#SBATCH --output=af3-score-%A.out

# Exit when any command fails
set -e

script_path=$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")
if ! [[ -f "${script_path}/af3-score.sh" ]] && [[ -n "$SLURM_JOB_ID" ]]
then
  script_path=$(dirname "$(scontrol show job "$SLURM_JOB_ID" | awk -F '=' '$0 ~ /Command=/ {print $2; exit}')")
fi
export SCRIPT_PATH="$script_path"

source "${script_path}/pairs-env/bin/activate"

echo "Running af3-score with parameters $*"
af3-score "$@"
