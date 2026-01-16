import argparse
import json
import os
import random
import re
from typing import TextIO

from Bio import SeqIO, SeqRecord

from pairs import FastaId


def readable_file(filepath: str):
  """Checks if a file exists and is readable, or if it's "-" for stdin."""
  if filepath == "-":
    return filepath # Special case for stdin/stdout path name

  if not os.path.exists(filepath):
    # Raise ArgumentTypeError to make argparse show a clean error message
    raise argparse.ArgumentTypeError(f"File not found: {filepath}")

  if not os.access(filepath, os.R_OK):
    raise argparse.ArgumentTypeError(f"File not readable: {filepath}")

  # If all checks pass, return the original string (the filepath)
  return filepath

def dir_path(string: str):
  if not string or os.path.isdir(string):
    return string
  else:
    raise NotADirectoryError(string)


def main(argv: list[str] = None):
  parser = argparse.ArgumentParser(
      description="Create JSON files for AlphaFold 3, each one containing a protein pair, "
                  "one protein from baits and one protein from targets file.")
  parser.add_argument('-b', '--baits', type=readable_file, required=True,
                      help="FASTA file containing baits")
  parser.add_argument('-t', '--targets', type=readable_file, required=True,
                      help="FASTA file containing targets")
  parser.add_argument('-s', '--seed', type=int, nargs="*", default=None,
                      help="Seed(s) to use for model inference.  (default: use random seed)")
  parser.add_argument('-u', '--unique', action='store_true',
                      help="Save only one JSON file per pair "
                           "- do not save POLR2B-POLR2A pair if POLR2A-POLR2B is also present.")
  parser.add_argument('-i', '--identity', action='store_true',
                      help="Don't save JSON file of a protein with itself "
                           "- same protein is present in both baits and targets.")
  parser.add_argument('-o', '--output', type=dir_path, default="",
                      help="Directory where to write JSON files.  (default: current directory)")

  args = parser.parse_args(argv)

  json_pairs(baits_file=args.baits, targets_file=args.targets, seeds=args.seed,
             unique=args.unique, skip_identity=args.identity,
             output=args.output)


def json_pairs(baits_file: str, targets_file: str, seeds: list[int] = None,
    unique: bool = False,
    skip_identity: bool = False, output: str = ""):
  """
  Create JSON files, each one containing a protein pair, one protein from baits and one protein from targets file.

  :param baits_file: FASTA file containing baits
  :param targets_file: FASTA file containing targets
  :param seeds: seeds to use for model inference
  :param unique: save only one JSON file per unique pair -
                 do not save POLR2B-POLR2A pair if POLR2A-POLR2B is also present
  :param skip_identity: don't save JSON file of a protein with itself -
                        if the same protein is present in both baits and targets
  :param output: where to write JSON files
  """
  with open(baits_file, "r") as baits_file_in:
    baits = parse_fasta(baits_file_in)
  with open(targets_file, "r") as targets_file_in:
    targets = parse_fasta(targets_file_in)

  processed_ids = set()
  for bait in baits:
    bait_id = re.sub(r"[^A-Za-z]", "", bait.split("_")[0])
    bait_data = {"protein": {"id": bait_id, "sequence": str(baits[bait].seq)}}
    for target in targets:
      if skip_identity and bait == target:
        continue
      reverse_id = f"{target}__{bait}"
      if unique and reverse_id in processed_ids:
        continue
      target_id = re.sub(r"[^A-Za-z]", "", target.split("_")[0])
      if target_id == bait_id:
        target_id = target_id + "A"
      target_data = {
        "protein": {"id": target_id, "sequence": str(targets[target].seq)}}
      merge_id = f"{bait}__{target}"
      json_data = {"name": merge_id,
                   "modelSeeds": seeds if seeds else [random.randint(1,
                                                                     2147483647)],
                   "dialect": "alphafold3", "version": 1,
                   "sequences": [bait_data, target_data]}
      with open(os.path.join(output, f"{merge_id}.json"), 'w') as output_file:
        output_file.write(json.dumps(json_data, indent=4))
      processed_ids.add(merge_id)


def parse_fasta(fasta: TextIO) -> dict[str, SeqRecord]:
  """
  Parses FASTA and returns all sequences found in file mapped by ID.

  The ID of each sequence is found using :func:`FastaId.fasta_id`

  :param fasta: FASTA file
  :return: all sequences found in file mapped by ID
  """
  sequences = {}
  for record in SeqIO.parse(fasta, "fasta"):
    seq_id = FastaId.fasta_id(record.description)
    sequences[seq_id] = record
  return sequences


if __name__ == '__main__':
  main()
