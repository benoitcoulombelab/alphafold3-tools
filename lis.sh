#!/bin/bash
#SBATCH --account=def-coulomb
#SBATCH --time=1-00:00:00
#SBATCH --cpus-per-task=24
#SBATCH --mem=40G
#SBATCH --output=lis-%A.out

# Exit when any command fails
set -e

script_name=$(basename "${BASH_SOURCE[0]}")
script_path=$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")
if ! [[ -f "${script_path}/lis.sh" ]] && [[ -n "$SLURM_JOB_ID" ]]
then
  slurm_command=$(scontrol show job "$SLURM_JOB_ID" | awk -F '=' '$0 ~ /Command=/ {print $2; exit}')
  script_name=$(basename "$slurm_command")
  script_path=$(dirname "$slurm_command")
fi
threads=${SLURM_CPUS_PER_TASK:-1}

# Usage function
usage() {
  echo
  echo "Usage: $script_name [-w int] [-h]"
  echo "  -w, --workers: Number of threads (default: 1 or SLURM_CPUS_PER_TASK if present)"
  echo "  -h, --help: Show this help"
}

# Parsing arguments.
while [ "$1" != "" ]; do
  case $1 in
    -w | --workers)	shift
      threads=$1
      ;;
    -h | --help)
      usage
      exit 0
      ;;
    *)
      extra_parameters+=("$1")
  esac
  shift
done

source "${script_path}/af3-tools-env/bin/activate"

echo "Running lis.py with parameters --workers $threads ${extra_parameters[*]}"
python "${script_path}/lis.py" --workers "$threads" "${extra_parameters[@]}"
