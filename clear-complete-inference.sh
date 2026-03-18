#!/bin/bash
#SBATCH --account=def-coulomb
#SBATCH --time=12:00:00
#SBATCH --cpus-per-task=24
#SBATCH --mem=24G
#SBATCH --mail-type=NONE
#SBATCH --output=clear-complete-inference-%A.out

# Exit when any command fails
set -e

script_name=$(basename "${BASH_SOURCE[0]}")

data_folder=data
inference_folder=structures
threads=${SLURM_CPUS_PER_TASK:-1}

# Usage function
usage() {
  echo
  echo "Usage: $script_name [-d <data_folder>] [-i <inference_folder>] [-h]"
  echo "  -d: Folder containing JSON input files from alphafold3-inference  (default: data)"
  echo "  -i: Folder containing output files for alphafold3-inference  (default: structures)"
  echo "  -t: Number of threads (default: 1 or SLURM_CPUS_PER_TASK if present)"
  echo "  -h: Show this help"
}

# Parsing arguments.
while getopts 'd:i:t:h' OPTION; do
  case "$OPTION" in
    d)
       data_folder="$OPTARG"
       ;;
    i)
       inference_folder="$OPTARG"
       ;;
    t)
       threads="$OPTARG"
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
if ! [[ -d "$data_folder" ]]
then
  >&2 echo "Error: -d parameter '$data_folder' is not a directory."
  usage
  exit 1
fi
if ! [[ -d "$inference_folder" ]]
then
  >&2 echo "Error: -i parameter '$inference_folder' is not a directory."
  usage
  exit 1
fi
if ! [[ "$threads" =~ ^[0-9]+$ ]]
then
  >&2 echo "Error: -t parameter '$threads' is not an integer."
  usage
  exit 1
fi


echo -e "\n\nDelete JSON input files for completed inference\n\n"

process_json() {
  local data_folder=$1
  local inference_folder=$2
  local input_json=$3
  local json_validation=0
  local output_json_exists=""
  local json_filename
  local output_directory
  json_filename=$(basename "$input_json" _data.json)
  output_directory="${inference_folder}/${json_filename}"
  for output_json in "$output_directory"/**/*.json
  do
    output_json_exists="true"
    python -mjson.tool "$output_json" > /dev/null 2>&1
    output_json_validation_result=$?
    if [[ "$output_json_validation_result" != 0 ]]
    then
      >&2 echo "Warning: '$output_json' is not a valid JSON file."
    fi
    json_validation=$((json_validation + output_json_validation_result))
  done
  if [[ -n "$output_json_exists" ]] && [[ "$json_validation" == 0 ]]
  then
    echo "Deleting file $input_json, output JSON files in $output_directory are valid"
    input_json_directory=$(dirname "$input_json")
    rm -f "$input_json"
    if [[ -z "$(ls -A "$input_json_directory")" ]]
    then
      rmdir "$input_json_directory"
    fi
  fi
}
export -f process_json

find "$data_folder" -name "*.json" \
 | parallel --jobs "$threads" --env process_json process_json "$data_folder" "$inference_folder"
