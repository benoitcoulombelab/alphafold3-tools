#!/bin/bash
#SBATCH --account=def-coulomb
#SBATCH --time=12:00:00
#SBATCH --cpus-per-task=24
#SBATCH --mem=24G
#SBATCH --mail-type=NONE
#SBATCH --output=alphafold3_clear_complete_data-%A.out

# Exit when any command fails
set -e

json_folder=json
data_folder=data

# Usage function
usage() {
  echo
  echo "Usage: alphafold3_clear_complete_data.sh [-j json] [-d data]"
  echo "  -j: Folder containing JSON input files for alphafold3_data  (default: json)"
  echo "  -d: Folder containing JSON output files from alphafold3_data  (default: data)"
  echo "  -h: Show this help"
}

# Parsing arguments.
while getopts 'j:d:h' OPTION; do
  case "$OPTION" in
    j)
       json_folder="$OPTARG"
       ;;
    d)
       data_folder="$OPTARG"
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
if ! [[ -d "$json_folder" ]]
then
  >&2 echo "Error: -j parameter '$json_folder' is not a directory."
  usage
  exit 1
fi
if ! [[ -d "$data_folder" ]]
then
  >&2 echo "Error: -d parameter '$data_folder' is not a directory."
  usage
  exit 1
fi


echo -e "\n\nDelete JSON input files for completed data\n\n"

process_json() {
  local json_folder=$1
  local data_folder=$2
  local input_json=$3
  local json_filename
  json_filename=$(basename "$input_json")
  json_filename="${json_filename%.*}"
  json_filename=$(tr "[:upper:]" "[:lower:]" <<< "$json_filename")
  local output_json="${data_folder}/${json_filename}/${json_filename}_data.json"
  if [[ -s "$output_json" ]]
  then
    python -mjson.tool "$output_json" > /dev/null 2>&1
    local json_validation=$?
    if [[ "$json_validation" == 0 ]]
    then
      echo "Deleting file $input_json, output file $output_json is complete"
      rm -f "$input_json"
    fi
  fi
}
export -f process_json

find "$json_folder" -name "*.json" \
 | parallel --env process_json process_json "$json_folder" "$data_folder"
