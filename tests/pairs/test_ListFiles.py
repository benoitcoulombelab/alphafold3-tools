import os
import shutil
import sys
from io import TextIOWrapper
from pathlib import Path
from unittest.mock import MagicMock, ANY, patch

import pytest

from pairs import ListFiles


@pytest.fixture
def mock_testclass():
  _list_files = ListFiles.list_files
  yield
  ListFiles.list_files = _list_files


def create_alphafold3_files(alphafold_output, name):
  create_files = [f"{name}_confidences.json", f"{name}_data.json",
                  f"{name}_model.cif",
                  f"{name}_summary_confidences.json", "ranking_scores.csv",
                  "TERMS_OF_USE.md"]
  [open(os.path.join(alphafold_output, file), 'w') for file in create_files]
  sample_folders = ["seed-1_sample-0", "seed-1_sample-1", "seed-1_sample-2",
                    "seed-1_sample-3", "seed-1_sample-4"]
  create_sample_files = ["confidences.json", "model.cif",
                         "summary_confidences.json"]
  for sample_folder in sample_folders:
    os.mkdir(os.path.join(alphafold_output, sample_folder))
    [open(os.path.join(alphafold_output, sample_folder, file), 'w') for file in
     create_sample_files]


def test_main(testdir, mock_testclass):
  ListFiles.list_files = MagicMock()
  ListFiles.main([])
  ListFiles.list_files.assert_called_once_with(
      input_dir="", output_file=ANY, progress=False)
  output_file = ListFiles.list_files.call_args.kwargs["output_file"]
  assert isinstance(output_file, TextIOWrapper)
  assert output_file.mode in ["r+", "w"]


def test_main_parameters(testdir, mock_testclass):
  input_dir = "alphafold"
  output_file = "output.txt"
  testdir.mkdir(input_dir)
  ListFiles.list_files = MagicMock()
  ListFiles.main(["-o", output_file, "-p", input_dir])
  ListFiles.list_files.assert_called_once_with(
      input_dir=input_dir, output_file=ANY, progress=True)
  output_file_arg = ListFiles.list_files.call_args.kwargs["output_file"]
  assert isinstance(output_file_arg, TextIOWrapper)
  assert output_file_arg.mode in ["r+", "w"]
  assert output_file_arg.name == output_file


def test_main_long_parameters(testdir, mock_testclass):
  input_dir = "alphafold"
  output_file = "output.txt"
  testdir.mkdir(input_dir)
  ListFiles.list_files = MagicMock()
  ListFiles.main(
      ["--output", output_file, "--progress", input_dir])
  ListFiles.list_files.assert_called_once_with(
      input_dir=input_dir, output_file=ANY, progress=True)
  output_file_arg = ListFiles.list_files.call_args.kwargs["output_file"]
  assert isinstance(output_file_arg, TextIOWrapper)
  assert output_file_arg.mode in ["r+", "w"]
  assert output_file_arg.name == output_file


def test_main_input_not_exists(testdir, mock_testclass):
  input_dir = "alphafold"
  output_file = "output.txt"
  ListFiles.list_files = MagicMock()
  with pytest.raises(NotADirectoryError):
    ListFiles.main(["-o", output_file, input_dir])
  ListFiles.list_files.assert_not_called()


def test_list_files_alphafold3(testdir, mock_testclass):
  alphafold_outputs = ["RPB1_RPB2", "RPB3_RPB4", "RPB5_RPB6", "RPB7_RPB8"]
  [testdir.mkdir(output) for output in alphafold_outputs]
  [create_alphafold3_files(output, output) for output in alphafold_outputs]
  [shutil.copy(Path(__file__).parent.joinpath("ranking_scores.csv"),
               f"{output}/ranking_scores.csv") for output in alphafold_outputs]
  output_file = "output.txt"
  with open(output_file, 'w') as output_out:
    ListFiles.list_files("", output_out)
  with open(output_file, 'r') as output_in:
    files = output_in.readlines()
  files = [file.rstrip('\r\n') for file in files]
  [print(file) for file in files]
  for output in alphafold_outputs:
    assert f"{output}/{output}_confidences.json" in files
    assert f"{output}/{output}_data.json" in files
    assert f"{output}/{output}_model.cif" in files
    assert f"{output}/{output}_summary_confidences.json" in files
    assert f"{output}/ranking_scores.csv" in files
    assert f"{output}/TERMS_OF_USE.md" in files


def test_list_files_progress(testdir, mock_testclass):
  alphafold_outputs = ["RPB1_RPB2", "RPB3_RPB4"]
  [testdir.mkdir(output) for output in alphafold_outputs]
  [create_alphafold3_files(output, output) for output in alphafold_outputs]
  [shutil.copy(Path(__file__).parent.joinpath("ranking_scores.csv"),
               f"{output}/ranking_scores.csv") for output in alphafold_outputs]
  output_file = "output.txt"
  with open(output_file, 'w') as output_out, patch("tqdm.tqdm",
                                                   return_value=alphafold_outputs) as mock_tqdm:
    ListFiles.list_files("", output_out, progress=True)
    mock_tqdm.assert_called_once_with(ANY)
    assert len(mock_tqdm.call_args.args[0]) == len(alphafold_outputs)
    for alphafold_output in alphafold_outputs:
      assert alphafold_output in mock_tqdm.call_args.args[0]
  with open(output_file, 'r') as output_in:
    files = output_in.readlines()
  files = [file.rstrip('\r\n') for file in files]
  [print(file) for file in files]
  for output in alphafold_outputs:
    assert f"{output}/{output}_confidences.json" in files
    assert f"{output}/{output}_data.json" in files
    assert f"{output}/{output}_model.cif" in files
    assert f"{output}/{output}_summary_confidences.json" in files
    assert f"{output}/ranking_scores.csv" in files
    assert f"{output}/TERMS_OF_USE.md" in files


def test_list_files_std_out(testdir, mock_testclass, capsys):
  alphafold_outputs = ["RPB1_RPB2", "RPB3_RPB4"]
  [testdir.mkdir(output) for output in alphafold_outputs]
  [create_alphafold3_files(output, output) for output in alphafold_outputs]
  [shutil.copy(Path(__file__).parent.joinpath("ranking_scores.csv"),
               f"{output}/ranking_scores.csv") for output in alphafold_outputs]
  ListFiles.list_files("", sys.stdout)
  out, err = capsys.readouterr()
  files = out.rstrip('\r\n').split("\n")
  files = [file.rstrip('\r\n') for file in files]
  [print(file) for file in files]
  for output in alphafold_outputs:
    assert f"{output}/{output}_confidences.json" in files
    assert f"{output}/{output}_data.json" in files
    assert f"{output}/{output}_model.cif" in files
    assert f"{output}/{output}_summary_confidences.json" in files
    assert f"{output}/ranking_scores.csv" in files
    assert f"{output}/TERMS_OF_USE.md" in files
