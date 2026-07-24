#!/bin/bash
#SBATCH --account=def-coulomb
#SBATCH --time=1-00:00:00
#SBATCH --cpus-per-task=24
#SBATCH --mem=90G
#SBATCH --output=lis-%A.out

# Exit when any command fails
set -e

script_path=$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")
if ! [[ -f "${script_path}/lis.sh" ]] && [[ -n "$SLURM_JOB_ID" ]]
then
  script_path=$(dirname "$(scontrol show job "$SLURM_JOB_ID" | awk -F '=' '$0 ~ /Command=/ {print $2; exit}')")
fi
threads=${SLURM_CPUS_PER_TASK:-1}

source "${script_path}/af3-tools-env/bin/activate"

echo "Running lis.py with parameters --workers $threads $*"
python "${script_path}/lis.py" --workers "$threads" "$@"
