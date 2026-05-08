#!/bin/bash

# Exit when any command fails
set -e

script_path=$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")
cd "$script_path" || exit 1

echo "Finding AlphaFold 3 requirements"

module purge
module load StdEnv/2023 hmmer-alphafold3/3.4 rdkit/2025.09.4 python/3.14

wget -O run_alphafold.py https://raw.githubusercontent.com/google-deepmind/alphafold3/refs/tags/v3.0.2/run_alphafold.py

virtualenv --no-download ./alphafold3_env
source ./alphafold3_env/bin/activate

pip install --no-index --upgrade pip
pip install --no-index alphafold3==3.0.2

build_data

pip freeze > ./alphafold3-requirements.txt

deactivate

rm -r ./alphafold3_env

echo "AlphaFold 3 requirements saved successfully"
