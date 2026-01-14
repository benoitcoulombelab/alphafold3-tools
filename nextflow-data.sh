#!/bin/bash
#SBATCH --account=def-coulomb
#SBATCH --time=7-00:00:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --output=nextflow-data-%A.out

# Exit when any command fails
set -e

script_path=$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")
if ! [[ -f "${script_path}/nextflow-data.sh" ]] && [[ -n "$SLURM_JOB_ID" ]]
then
  script_path=$(dirname "$(scontrol show job "$SLURM_JOB_ID" | awk -F '=' '$0 ~ /Command=/ {print $2; exit}')")
fi

export SCRIPT_PATH="$script_path"

echo "Launching nextflow pipeline ${script_path}/alphafold3_data.nf"
nextflow run ${script_path}/alphafold3_data.nf -c "${script_path}/alphafold3.config" \
    "$@"
