import argparse
import glob
import os
import sys
from typing import TextIO

import tqdm


RANKING_FILES = ["ranking_scores.csv"]


def dir_path(string: str):
  if not string or os.path.isdir(string):
    return string
  else:
    raise NotADirectoryError(string)


def main(argv: list[str] = None):
  parser = argparse.ArgumentParser(
      description="List files from AlphaFold 3's output that need to be archived.")
  parser.add_argument('input', nargs='?', type=dir_path, default="",
                      help="Directory containing one or many AlphaFold's output directories  "
                           "(default: current directory)")
  parser.add_argument('-o', '--output', type=argparse.FileType('w'),
                      default=sys.stdout,
                      help="Output file  (default: standard output)")
  parser.add_argument('-p', '--progress', action="store_true", default=False,
                      help="Show progress bar")

  args = parser.parse_args(argv)

  list_files(input_dir=args.input, output_file=args.output,
             progress=args.progress)


def list_files(input_dir: str, output_file: TextIO, progress: bool = False):
  """
  List files from AlphaFold 3's output that need to be archived.

  :param input_dir: directory containing one or many AlphaFold's output directories
  :param output_file: output file
  :param progress: show progress bar
  """
  ranking_files = []
  [ranking_files.extend(
      glob.glob(os.path.join(input_dir, f"**/{ranking_file}"))) for ranking_file
    in RANKING_FILES]
  directories = [os.path.dirname(ranking_file) for ranking_file in
                 ranking_files]
  directories = list(set(directories))
  directories.sort()
  for directory in (tqdm.tqdm(directories) if progress else directories):
    ranking_files = []
    [ranking_files.extend(glob.glob(os.path.join(directory, ranking_file))) for
     ranking_file in RANKING_FILES]
    ranking_files.sort()
    files_to_archive = glob.glob(os.path.join(directory, "*.json"))
    files_to_archive.extend(glob.glob(os.path.join(directory, "*.cif")))
    files_to_archive.append(ranking_files[0])
    files_to_archive.append(os.path.join(directory, "TERMS_OF_USE.md"))
    files_to_archive = list(set(files_to_archive))
    files_to_archive.sort()
    for file in files_to_archive:
      output_file.write(file)
      output_file.write("\n")


if __name__ == '__main__':
  main()
