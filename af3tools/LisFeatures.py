import argparse
import csv
import json
import os
import sys

import tqdm


def readable_file(filepath: str):
  """Checks if a file exists and is readable, or if it's "-" for stdin."""
  if filepath == "-":
    return filepath  # Special case for stdin/stdout path name

  if not os.path.exists(filepath):
    # Raise ArgumentTypeError to make argparse show a clean error message
    raise argparse.ArgumentTypeError(f"File not found: {filepath}")

  if not os.access(filepath, os.R_OK):
    raise argparse.ArgumentTypeError(f"File not readable: {filepath}")

  # If all checks pass, return the original string (the filepath)
  return filepath


def writable_path(filepath: str):
  """Checks if the path is potentially writable, or if it's '-' for stdout."""
  if filepath == "-":
    return filepath  # Special case for stdin/stdout path name

  # Check if directory exists (and create it if you want, but simple check is enough)
  # A simple check for writability can be complex, so for most CLI tools,
  # just returning the string is fine, and let 'open()' handle the creation/error.
  # We'll just return the string for simplicity here.
  return filepath


def dir_path(string: str):
  if not string or os.path.isdir(string):
    return string
  else:
    raise NotADirectoryError(string)


NAME_COLUMN = "name"
CHAIN_I_COLUMN = "chain_i"
CHAIN_J_COLUMN = "chain_j"
BAIT_COLUMN = "bait"
TARGET_COLUMN = "target"


def main(argv: list[str] = None):
  parser = argparse.ArgumentParser(
    description="Add bait and target information to a lis.py output file.")
  parser.add_argument("-l", "--lis", type=readable_file,
                      default="structures/structures_lis_analysis.csv",
                      help="File containing LIS scores - created by lis.py  (default: %(default)s)")
  parser.add_argument("-a", "--alphafold", type=dir_path, default="structures",
                      help="Directory to look for AlphaFold 3 data JSON files  (default: %(default)s)")
  parser.add_argument("-o", "--output", type=writable_path, default="-",
                      help="CSV output file containing lis.py output plus baits and targets  (default: standard output '-')")
  parser.add_argument("-p", "--progress", action="store_true", default=False,
                      help="Show progress bar")

  args = parser.parse_args(argv)

  add_bait_target(lis_file=args.lis, alphafold_dir=args.alphafold,
                  output_file=args.output,
                  progress=args.progress)


def add_bait_target(lis_file: str = "structures/structures_lis_analysis.csv",
    alphafold_dir: str = "structures",
    output_file: str = "-",
    progress: bool = False):
  """
  Add bait and target information to a lis.py output file.

  :param lis_file: File containing LIS scores - created by lis.py
  :param alphafold_dir: Directory to look for AlphaFold 3 data JSON files  (default: current directory)
  :param output_file: CSV output file containing lis.py output plus baits and targets  (default: standard output '-')
  :param progress: if True, show progress bar
  """
  if not lis_file:
    raise AssertionError("lis_file parameter is required")

  # Parse LIS files.
  all_lis = parse_lis(lis_file)

  # Prepare output columns.
  output_fieldnames = list(all_lis[0].keys())
  output_fieldnames.insert(0, TARGET_COLUMN)
  output_fieldnames.insert(0, BAIT_COLUMN)

  # Find bait and target for each entry.
  for lis in tqdm.tqdm(
      all_lis) if progress else all_lis:
    bait, target = get_bait_target(lis, alphafold_dir)
    lis[BAIT_COLUMN] = bait
    lis[TARGET_COLUMN] = target

  # Write to output.
  with open(output_file,
            "w") if output_file != "-" else sys.stdout as output_file_out:
    writer = csv.DictWriter(output_file_out, fieldnames=output_fieldnames)
    writer.writeheader()
    for lis in all_lis:
      writer.writerow(lis)


def get_bait_target(lis: dict[str, str], alphafold_dir: str) -> tuple[str, str]:
  """
  Returns LIS entry with bait and target columns added.

  :param lis: lis.py entry
  :param alphafold_dir: Directory to look for AlphaFold 3 data JSON files  (default: current directory)
  :return: a tuple contain bait and target
  """
  name = lis[NAME_COLUMN]
  features = name.split("__")
  chain_i = lis[CHAIN_I_COLUMN]
  chain_j = lis[CHAIN_J_COLUMN]
  # Find AlphaFold 3 data file for each LIS entries.
  data_file = os.path.join(alphafold_dir, name, name + "_data.json")
  if not os.path.isfile(data_file):
    raise FileNotFoundError(data_file)
  sequence_ids = get_sequence_ids(data_file)
  chain_i_index = sequence_ids.index(chain_i)
  chain_j_index = sequence_ids.index(chain_j)
  bait = features[chain_i_index]
  target = features[chain_j_index]
  if chain_i_index > chain_j_index:
    bait = features[chain_j_index]
    target = features[chain_i_index]
  return bait, target


def get_sequence_ids(data_file: str) -> list[str]:
  """
  Returns id of all sequences in the *_data.json file.

  :param data_file: data JSON file
  :return: list containing all sequence ids in order
  """
  ids = []
  data = load_json(data_file)
  for sequence in data["sequences"]:
    sequence_type = next(iter(sequence.keys()))
    sequence_id = sequence[sequence_type]["id"]
    ids.append(sequence_id)
  return ids


def parse_lis(lis_file: str) \
    -> list[dict[str, str]]:
  """
  Parse file containing LIS scores.

  :param lis_file: file containing LIS scores - created by lis.py
  :return: dictionary of source id to converted id
  """
  all_lis = []
  with open(lis_file, "r") if lis_file != "-" else sys.stdin as lis_file_in:
    for row in csv.DictReader(lis_file_in):
      all_lis.append(row)
  return all_lis


def load_json(file) -> dict:
  with open(file, "r") as file_in:
    return json.load(file_in)


if __name__ == "__main__":
  main()
