#!/bin/bash

# Exit when any command fails
set -e

script_name=$(basename "${BASH_SOURCE[0]}")
current_directory=$(pwd)

# Default argument values.
version=v3.0.2
development=
requirements=alphafold3-requirements.txt
patch=

# Usage function
usage() {
  echo
  echo "Creates AlphaFold 3 python wheel"
  echo
  echo "Usage: $script_name [-v <version>] [-p <patch>] [-d] [-r <requirements>] [-h]"
  echo "  -v: Version (tag or commit hash) of AlphaFold 3 to create wheel for (default: v3.0.2)"
  echo "  -p: Patch file to apply before creating wheel (default: none)"
  echo "  -d: Version is a development, '-dev' will be appended to the version (default: '-dev' not appended)"
  echo "  -r: PIP requirements output (default: alphafold3-requirements.txt)"
  echo "  -h: Show this help and squire Map help"
  echo
  echo "This script needs to be adapted to work on specific versions and commits and will work only"
  echo "on Alliance Canada clusters for commits around version v3.0.2"
  echo
}

# Parsing arguments.
while getopts 'v:p:dr:h' OPTION; do
  case "$OPTION" in
    v)
       version="$OPTARG"
       ;;
    p)
       patch="$OPTARG"
       ;;
    d)
       development=true
       ;;
    r)
       requirements="$OPTARG"
       ;;
    h)
       usage
       exit 0
       ;;
    :)
       usage
       exit 1
       ;;
    ?)
       usage
       exit 1
       ;;
  esac
done

# Validating arguments.
if [[ -n "$patch" ]] && ! [[ -f "$patch" ]]
then
  >&2 echo "Error: -p parameter $patch is not a file."
  usage
  exit 1
fi


module purge
module load StdEnv/2023
module load rdkit/2025.09.4 python/3.14 cmake

tmp_dir=$(mktemp -d "${TMPDIR:-/tmp}/$(basename "$0").XXXXXXXXXXXX")
trap 'rm -rf "$tmp_dir"; exit' ERR EXIT

echo "Creating python virtualenv"
virtualenv --clear "${tmp_dir}/AF3-ENV" && source "${tmp_dir}/AF3-ENV/bin/activate"
pip install -U pip

echo "Cloning AlphaFold 3 version $version"
git clone https://github.com/google-deepmind/alphafold3.git "${tmp_dir}/alphafold3"
cd "${tmp_dir}/alphafold3"
git checkout "$version"
if [[ -n "$patch" ]]
then
  echo "Applying patch $patch to AlphaFold 3 version $version"
  git apply "$patch"
fi
if [[ -n "$development" ]]
then
  sed -i 's/\(version = "[0-9.]*\)"/\1-dev"/' pyproject.toml
fi

echo "Build AlphaFold 3 wheel"
CMAKE_BUILD_PARALLEL_LEVEL=8 pip wheel --no-deps --no-index -v .
wheels=(alphafold3*.whl)
if [[ -f "${wheels[0]}" ]]
then
  wheel=${wheels[0]}
else
  >&2 echo "Error: failed to create wheel for AlphaFold 3, exiting..."
  exit 1
fi

echo "Creating pip requirements file"
cp "$wheel" "$current_directory"
pip install --no-index "$current_directory/$wheel"
pip freeze --local > "${tmp_dir}/${requirements}"

deactivate

cp "run_alphafold.py" "$current_directory"
cp "${tmp_dir}/${requirements}" "$current_directory"

echo
echo "Copied AlphaFold 3 wheel '$wheel', 'run_alphafold.py' and pip requirements '$requirements'"
