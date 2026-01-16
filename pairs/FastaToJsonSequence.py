import argparse
import json
import os
import random
import re
import sys
from typing import TextIO, Any

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
      description="Create a `sequence` JSON element for AlphaFold 3 for each sequence found in FASTA files.")
  parser.add_argument("-f", "--fasta", nargs="*", type=readable_file, default=["-"],
                      help="FASTA file(s).  (default: stdin)")
  parser.add_argument("-o", "--output", type=dir_path, default="",
                      help="Directory where to write JSON files.  (default: current directory)")

  args = parser.parse_args(argv)

  fasta_to_json_sequence(fasta_files=args.fasta, output_dir=args.output)


def fasta_to_json_sequence(fasta_files: list[str], output_dir: str = ""):
  """
  Create a JSON sequence files for AlphaFold 3 for each sequence found in FASTA files.

  :param fasta_files: FASTA files
  :param output_dir: where to write JSON sequence files
  """
  for fasta_file in fasta_files:
    fasta_file = sys.stdin if fasta_file == "-" else fasta_file
    with open(fasta_file, "r") as fasta_in:
      sequences = parse_fasta(fasta_in)
    for sequence in sequences:
      json_data = sequence_to_json(sequence, sequences[sequence])
      with open(os.path.join(output_dir, f"{sequence}.json"), 'w') as output_file:
        output_file.write(json.dumps(json_data, indent=4))


def sequence_to_json(sequence_id: str, sequence: SeqRecord) -> dict:
  """
  Create a JSON sequence element based on sequence.

  :param sequence_id: sequence ID
  :param sequence: sequence record
  :return: JSON sequence element
  """
  id_element = re.sub(r"[^A-Za-z]", "", sequence_id.split("_")[0])
  return {"protein": {"id": id_element,
                      "sequence": str(sequence.seq),
                      "description": sequence_id}}


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
