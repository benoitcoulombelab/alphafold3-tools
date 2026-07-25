import io
import os
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from af3tools import af3lis


@pytest.fixture
def mock_testclass():
  _af3_score = af3lis.af3_score
  _parse_lis = af3lis.parse_lis
  _get_confidence_scores = af3lis.get_confidence_scores
  _get_sequence_ids = af3lis.get_sequence_ids
  _parse_mapping = af3lis.parse_mapping
  yield
  af3lis.af3_score = _af3_score
  af3lis.parse_lis = _parse_lis
  af3lis.get_confidence_scores = _get_confidence_scores
  af3lis.get_sequence_ids = _get_sequence_ids
  af3lis.parse_mapping = _parse_mapping


def create_alphafold3_files(alphafold_output, name):
  create_files = [f"{name}_confidences.json", f"{name}_data.json",
                  f"{name}_model.cif",
                  f"{name}_summary_confidences.json", "ranking_scores.csv",
                  "TERMS_OF_USE.md"]
  [open(os.path.join(alphafold_output, file), "w") for file in create_files]
  sample_folders = ["seed-1_sample-0", "seed-1_sample-1", "seed-1_sample-2",
                    "seed-1_sample-3", "seed-1_sample-4"]
  create_sample_files = ["confidences.json", "model.cif",
                         "summary_confidences.json"]
  for sample_folder in sample_folders:
    os.mkdir(os.path.join(alphafold_output, sample_folder))
    [open(os.path.join(alphafold_output, sample_folder, file), "w") for file in
     create_sample_files]


def test_main(testdir, mock_testclass):
  lis_file = "structures/structures_lis_analysis.csv"
  Path(lis_file).parent.mkdir()
  Path(lis_file).touch()
  af3lis.af3_score = MagicMock()
  af3lis.main([])
  af3lis.af3_score.assert_called_once_with(
    input_dir="", output_file="-",
    name=r"([\w-]+)__([\w-]+)_summary_confidences",
    metrics=["iptm"],
    sequence_one=0, sequence_two=1,
    lis_file="structures/structures_lis_analysis.csv",
    progress=False,
    mapping_file=None, source_column=0, converted_column=1)


def test_main_parameters(testdir, mock_testclass):
  output = "output.txt"
  metrics = ["iptm", "lis"]
  name = r"(\w+)_(\w+)"
  mapping = "mapping.txt"
  Path(mapping).touch()
  sequence_one = 2
  sequence_two = 3
  lis_file = "lis.csv"
  Path(lis_file).touch()
  source_column = 2
  converted_column = 3
  af3lis.af3_score = MagicMock()
  af3lis.main(
    ["-i", str(testdir), "-o", output, "-m", metrics[0], metrics[1], "-n",
     name, "-1", str(sequence_one), "-2", str(sequence_two), "-l", lis_file,
     "-p", "-M", mapping, "-S", str(source_column + 1), "-C",
     str(converted_column + 1)])
  af3lis.af3_score.assert_called_once_with(
    input_dir=str(testdir), output_file=output, name=name,
    metrics=metrics,
    sequence_one=sequence_one - 1, sequence_two=sequence_two - 1,
    lis_file=lis_file,
    progress=True,
    mapping_file=mapping, source_column=source_column,
    converted_column=converted_column)


def test_main_long_parameters(testdir, mock_testclass):
  output = "output.txt"
  metrics = ["iptm", "lis"]
  name = r"(\w+)_(\w+)"
  mapping = "mapping.txt"
  Path(mapping).touch()
  sequence_one = 2
  sequence_two = 3
  lis_file = "lis.csv"
  Path(lis_file).touch()
  source_column = 2
  converted_column = 3
  af3lis.af3_score = MagicMock()
  af3lis.main(
    ["--input", str(testdir), "--output", output, "--metric", metrics[0],
     metrics[1],
     "--name", name, "--sequence1", str(sequence_one), "--sequence2",
     str(sequence_two), "--lis", lis_file, "--progress",
     "--mapping", mapping, "--source_column", str(source_column + 1),
     "--converted_column", str(converted_column + 1)])
  af3lis.af3_score.assert_called_once_with(
    input_dir=str(testdir), output_file=output, name=name,
    metrics=metrics,
    sequence_one=sequence_one - 1, sequence_two=sequence_two - 1,
    lis_file=lis_file,
    progress=True,
    mapping_file=mapping, source_column=source_column,
    converted_column=converted_column)


def test_main_no_metrics(testdir, mock_testclass):
  af3lis.af3_score = MagicMock()
  with pytest.raises(SystemExit):
    af3lis.main(["-m"])
  af3lis.af3_score.assert_not_called()


def test_af3_score(testdir, mock_testclass):
  confidence_file_1 = "POLR2A__POLR2B/POLR2A__POLR2B_summary_confidences.json"
  confidence_file_2 = "POLR2A__POLR2C/POLR2A__POLR2C_summary_confidences.json"
  Path(confidence_file_1).parent.mkdir()
  Path(confidence_file_2).parent.mkdir()
  shutil.copy(Path(__file__).parent.joinpath(
    "fab53__hvm62_mouse_summary_confidences.json"),
    confidence_file_1)
  shutil.copy(Path(__file__).parent.joinpath(
    "fab53__znrf1_mouse_summary_confidences.json"),
    confidence_file_2)
  output = "output.txt"
  af3lis.parse_mapping = MagicMock()
  all_lis = [
    af3lis.LIS("POLR2A__POLR2B", "POLR", "POLRB", 0.2, 0.12, 12300, 0.2, 0.3)]
  af3lis.parse_lis = MagicMock(side_effect=[all_lis])
  af3lis.get_confidence_scores = MagicMock(
    side_effect=[(confidence_file_1, [0.7772]), (confidence_file_2, [0.7601])])
  af3lis.af3_score(output_file=output)
  af3lis.parse_lis.assert_any_call("structures/structures_lis_analysis.csv")
  af3lis.get_confidence_scores.assert_any_call(confidence_file_1, ["iptm"],
                                               all_lis, 0, 1)
  af3lis.get_confidence_scores.assert_any_call(confidence_file_2, ["iptm"],
                                               all_lis, 0, 1)
  af3lis.parse_mapping.assert_not_called()
  with open(output, "r") as output_in:
    assert output_in.readline() == "Bait\tTarget\tipTM\n"
    assert output_in.readline() == "POLR2A\tPOLR2B\t0.7772\n"
    assert output_in.readline() == "POLR2A\tPOLR2C\t0.7601\n"


def test_af3_score_parameters(testdir, mock_testclass):
  testdir.mkdir("confidences")
  confidence_file_1 = "confidences/RPB-1___RPB-2/RPB-1___RPB-2_summary_confidences.json"
  confidence_file_2 = "confidences/RPB-1___RPB-3/RPB-1___RPB-3_summary_confidences.json"
  Path(confidence_file_1).parent.mkdir()
  Path(confidence_file_2).parent.mkdir()
  shutil.copy(Path(__file__).parent.joinpath(
    "fab53__hvm62_mouse_summary_confidences.json"),
    confidence_file_1)
  shutil.copy(Path(__file__).parent.joinpath(
    "fab53__znrf1_mouse_summary_confidences.json"),
    confidence_file_2)
  output = "output.txt"
  metrics = ["iptm", "lis"]
  mappings_file = "mappings.txt"
  Path(mappings_file).touch()
  lis_file = "lis.csv"
  mappings = {"RPB-1": "POLR2A", "RPB-2": "POLR2B", "RPB-3": "POLR2C"}
  af3lis.parse_mapping = MagicMock(return_value=mappings)
  all_lis = [
    af3lis.LIS("POLR2A__POLR2B", "POLR", "POLRB", 0.2, 0.12, 12300, 0.2, 0.3)]
  af3lis.parse_lis = MagicMock(side_effect=[all_lis])
  af3lis.get_confidence_scores = MagicMock(
    side_effect=[(confidence_file_1, [0.7772, 0.7059, 0.8952, 1200]),
                 (confidence_file_2, [0.7601, 0.783, 0.8985, 2400])])
  af3lis.af3_score("confidences", output,
                   r"([\w-]+)___([\w-]+)_summary_confidences",
                   metrics, 1, 2, lis_file, False, mappings_file,
                   2, 3)
  af3lis.parse_lis.assert_any_call(lis_file)
  af3lis.get_confidence_scores.assert_any_call(confidence_file_1, metrics,
                                               all_lis, 1,
                                               2)
  af3lis.get_confidence_scores.assert_any_call(confidence_file_2, metrics,
                                               all_lis, 1,
                                               2)
  af3lis.parse_mapping.assert_called_once_with(mappings_file, 2, 3)
  with open(output, "r") as output_in:
    assert output_in.readline() == "Bait\tTarget\tipTM\tiLIS\tLIS\tLIA\n"
    assert output_in.readline() == "POLR2A\tPOLR2B\t0.7772\t0.7059\t0.8952\t1200\n"
    assert output_in.readline() == "POLR2A\tPOLR2C\t0.7601\t0.783\t0.8985\t2400\n"


def test_af3_score_failure(testdir, mock_testclass):
  testdir.mkdir("confidences")
  confidence_file_1 = "confidences/RPB-1___RPB-2/RPB-1___RPB-2_summary_confidences.json"
  confidence_file_2 = "confidences/RPB-1___RPB-3/RPB-1___RPB-3_summary_confidences.json"
  Path(confidence_file_1).parent.mkdir()
  Path(confidence_file_2).parent.mkdir()
  shutil.copy(Path(__file__).parent.joinpath(
    "fab53__hvm62_mouse_summary_confidences.json"),
    confidence_file_1)
  shutil.copy(Path(__file__).parent.joinpath(
    "fab53__znrf1_mouse_summary_confidences.json"),
    confidence_file_2)
  output = "output.txt"
  metrics = ["iptm", "lis"]
  mappings_file = "mappings.txt"
  Path(mappings_file).touch()
  lis_file = "lis.csv"
  mappings = {"RPB-1": "POLR2A", "RPB-2": "POLR2B", "RPB-3": "POLR2C"}
  af3lis.parse_mapping = MagicMock(return_value=mappings)
  all_lis = [
    af3lis.LIS("POLR2A__POLR2B", "POLR", "POLRB", 0.2, 0.12, 12300, 0.2, 0.3)]
  af3lis.parse_lis = MagicMock(side_effect=[all_lis])
  af3lis.get_confidence_scores = MagicMock(
    side_effect=[(confidence_file_1, [0.7772, 0.7059, 0.8952, 1200]),
                 AssertionError("error on second call")])
  with pytest.raises(AssertionError):
    af3lis.af3_score("confidences", output,
                     r"([\w-]+)___([\w-]+)_summary_confidences",
                     metrics, 1, 2, lis_file, False, mappings_file,
                     2, 3)
  af3lis.get_confidence_scores.assert_any_call(confidence_file_1, metrics,
                                               all_lis, 1, 2)
  af3lis.get_confidence_scores.assert_any_call(confidence_file_2, metrics,
                                               all_lis, 1, 2)
  af3lis.parse_mapping.assert_called_once_with(mappings_file, 2, 3)


def test_af3_score_progress(testdir, mock_testclass):
  confidence_file_1 = "POLR2A__POLR2B/POLR2A__POLR2B_summary_confidences.json"
  confidence_file_2 = "POLR2A__POLR2C/POLR2A__POLR2C_summary_confidences.json"
  Path(confidence_file_1).parent.mkdir()
  Path(confidence_file_2).parent.mkdir()
  shutil.copy(Path(__file__).parent.joinpath(
    "fab53__hvm62_mouse_summary_confidences.json"),
    confidence_file_1)
  shutil.copy(Path(__file__).parent.joinpath(
    "fab53__znrf1_mouse_summary_confidences.json"),
    confidence_file_2)
  confidence_files = [confidence_file_1, confidence_file_2]
  output = "output.txt"
  af3lis.parse_mapping = MagicMock()
  all_lis = [
    af3lis.LIS("POLR2A__POLR2B", "POLR", "POLRB", 0.2, 0.12, 12300, 0.2, 0.3)]
  af3lis.parse_lis = MagicMock(side_effect=[all_lis])
  af3lis.get_confidence_scores = MagicMock(
    side_effect=[(confidence_file_1, [0.7772]), (confidence_file_2, [0.7601])])
  tqdm_list = confidence_files
  with patch("tqdm.tqdm", return_value=tqdm_list) as mock_tqdm:
    af3lis.af3_score(output_file=output,
                     progress=True)
    mock_tqdm.assert_called_once_with(confidence_files)
  af3lis.get_confidence_scores.assert_any_call(confidence_file_1, ["iptm"],
                                               all_lis, 0, 1)
  af3lis.get_confidence_scores.assert_any_call(confidence_file_2, ["iptm"],
                                               all_lis, 0, 1)
  af3lis.parse_mapping.assert_not_called()
  with open(output, "r") as output_in:
    assert output_in.readline() == "Bait\tTarget\tipTM\n"
    assert output_in.readline() == "POLR2A\tPOLR2B\t0.7772\n"
    assert output_in.readline() == "POLR2A\tPOLR2C\t0.7601\n"


def test_af3_score_empty_metrics(testdir, mock_testclass):
  confidence_file_1 = "POLR2A__POLR2B/POLR2A__POLR2B_summary_confidences.json"
  confidence_file_2 = "POLR2A__POLR2C/POLR2A__POLR2C_summary_confidences.json"
  Path(confidence_file_1).parent.mkdir()
  Path(confidence_file_2).parent.mkdir()
  shutil.copy(Path(__file__).parent.joinpath(
    "fab53__hvm62_mouse_summary_confidences.json"),
    confidence_file_1)
  shutil.copy(Path(__file__).parent.joinpath(
    "fab53__znrf1_mouse_summary_confidences.json"),
    confidence_file_2)
  output = "output.txt"
  af3lis.parse_mapping = MagicMock()
  af3lis.parse_lis = MagicMock()
  af3lis.get_confidence_scores = MagicMock(side_effect=[[0.7772], [0.7601]])
  with pytest.raises(AssertionError):
    af3lis.af3_score(output_file=output,
                     metrics=[])
  af3lis.get_confidence_scores.assert_not_called()
  af3lis.parse_lis.assert_not_called()
  af3lis.parse_mapping.assert_not_called()


def test_af3_score_invalid_metrics(testdir, mock_testclass):
  confidence_file_1 = "POLR2A__POLR2B/POLR2A__POLR2B_summary_confidences.json"
  confidence_file_2 = "POLR2A__POLR2C/POLR2A__POLR2C_summary_confidences.json"
  Path(confidence_file_1).parent.mkdir()
  Path(confidence_file_2).parent.mkdir()
  shutil.copy(Path(__file__).parent.joinpath(
    "fab53__hvm62_mouse_summary_confidences.json"),
    confidence_file_1)
  shutil.copy(Path(__file__).parent.joinpath(
    "fab53__znrf1_mouse_summary_confidences.json"),
    confidence_file_2)
  output = "output.txt"
  af3lis.parse_mapping = MagicMock()
  af3lis.parse_lis = MagicMock()
  af3lis.get_confidence_scores = MagicMock(side_effect=[[0.7772], [0.7601]])
  with pytest.raises(AssertionError):
    af3lis.af3_score(output_file=output,
                     metrics=["test"])
  af3lis.get_confidence_scores.assert_not_called()
  af3lis.parse_lis.assert_not_called()
  af3lis.parse_mapping.assert_not_called()


def test_get_confidence_scores_iptm(testdir, mock_testclass):
  confidence_file = "POLR2A__POLR2B/POLR2A__POLR2B_summary_confidences.json"
  Path(confidence_file).parent.mkdir()
  shutil.copy(Path(__file__).parent.joinpath(
    "fab53__hvm62_mouse_summary_confidences.json"),
    confidence_file)
  all_lis = [
    af3lis.LIS("POLR2A__POLR2B", "POLR", "POLRB", 0.2, 0.12, 12300, 0.7, 0.3),
    af3lis.LIS("POLR2A__POLR2B", "POLRB", "POLR", 0.2, 0.12, 12300, 0.2, 0.3),
    af3lis.LIS("POLR2A__POLR2C", "POLRB", "POLR", 0.2, 0.12, 12300, 0.9, 0.3),
    af3lis.LIS("POLR2A__POLR2B", "POLRC", "POLR", 0.2, 0.12, 12300, 0.9, 0.3),
  ]
  af3lis.get_sequence_ids = MagicMock(return_value=("POLR", "POLRB"))
  cf, scores = af3lis.get_confidence_scores(confidence_file, ["iptm"], all_lis)
  af3lis.get_sequence_ids.assert_called_once_with(confidence_file, 0, 1)
  assert cf == confidence_file
  assert len(scores) == 1
  assert scores[0] == pytest.approx(0.45)


def test_get_confidence_scores_ptm(testdir, mock_testclass):
  confidence_file = "POLR2A__POLR2B/POLR2A__POLR2B_summary_confidences.json"
  Path(confidence_file).parent.mkdir()
  shutil.copy(Path(__file__).parent.joinpath(
    "fab53__hvm62_mouse_summary_confidences.json"),
    confidence_file)
  all_lis = [
    af3lis.LIS("POLR2A__POLR2B", "POLR", "POLRB", 0.2, 0.12, 12300, 0.2, 0.3),
    af3lis.LIS("POLR2A__POLR2B", "POLRB", "POLR", 0.2, 0.12, 12300, 0.2, 0.8),
    af3lis.LIS("POLR2A__POLR2C", "POLRB", "POLR", 0.2, 0.12, 12300, 0.2, 0.9),
    af3lis.LIS("POLR2A__POLR2B", "POLRC", "POLR", 0.2, 0.12, 12300, 0.2, 0.9),
  ]
  af3lis.get_sequence_ids = MagicMock(return_value=("POLR", "POLRB"))
  cf, scores = af3lis.get_confidence_scores(confidence_file, ["ptm"], all_lis)
  af3lis.get_sequence_ids.assert_called_once_with(confidence_file, 0, 1)
  assert cf == confidence_file
  assert len(scores) == 1
  assert scores[0] == pytest.approx(0.55)


def test_get_confidence_scores_lis(testdir, mock_testclass):
  confidence_file = "POLR2A__POLR2B/POLR2A__POLR2B_summary_confidences.json"
  Path(confidence_file).parent.mkdir()
  create_alphafold3_files("POLR2A__POLR2B", "POLR2A__POLR2B")
  shutil.copy(Path(__file__).parent.joinpath(
    "fab53__hvm62_mouse_summary_confidences.json"),
    confidence_file)
  all_lis = [
    af3lis.LIS("POLR2A__POLR2B", "POLR", "POLRB", 0.3, 0.2,
               16000, 0.2, 0.3),
    af3lis.LIS("POLR2A__POLR2B", "POLR", "POLRB", 0.1, 0.1, 6000,
               0.2, 0.3),
    af3lis.LIS("POLR2A__POLR2C", "POLR", "POLRB", 0.9, 0.9,
               900000, 0.2, 0.3),
    af3lis.LIS("POLR2A__POLR2B", "POLRC", "POLR", 0.9, 0.9,
               900000, 0.2, 0.3),
    af3lis.LIS("POLR2A__POLR2B", "POLRB", "POLRC", 0.9, 0.9,
               900000, 0.2, 0.3),
  ]
  af3lis.get_sequence_ids = MagicMock(return_value=("POLR", "POLRB"))
  cf, scores = af3lis.get_confidence_scores(confidence_file, ["lis"], all_lis)
  af3lis.get_sequence_ids.assert_called_once_with(confidence_file, 0, 1)
  assert cf == confidence_file
  assert len(scores) == 3
  assert scores[0] == pytest.approx(0.2)
  assert scores[1] == pytest.approx(0.15)
  assert scores[2] == pytest.approx(11000)


def test_get_confidence_scores_iptm_ptm(testdir, mock_testclass):
  confidence_file = "POLR2A__POLR2B/POLR2A__POLR2B_summary_confidences.json"
  Path(confidence_file).parent.mkdir()
  shutil.copy(Path(__file__).parent.joinpath(
    "fab53__hvm62_mouse_summary_confidences.json"),
    confidence_file)
  all_lis = [
    af3lis.LIS("POLR2A__POLR2B", "POLR", "POLRB", 0.2, 0.12, 12300, 0.7, 0.3),
    af3lis.LIS("POLR2A__POLR2B", "POLRB", "POLR", 0.2, 0.12, 12300, 0.2, 0.8),
    af3lis.LIS("POLR2A__POLR2C", "POLRB", "POLR", 0.2, 0.12, 12300, 0.9, 0.9),
    af3lis.LIS("POLR2A__POLR2B", "POLRC", "POLR", 0.2, 0.12, 12300, 0.9, 0.9),
  ]
  af3lis.get_sequence_ids = MagicMock(return_value=("POLR", "POLRB"))
  cf, scores = af3lis.get_confidence_scores(confidence_file, ["iptm", "ptm"],
                                            all_lis)
  af3lis.get_sequence_ids.assert_called_once_with(confidence_file, 0, 1)
  assert cf == confidence_file
  assert len(scores) == 2
  assert scores[0] == pytest.approx(0.45)
  assert scores[1] == pytest.approx(0.55)


def test_get_confidence_scores_ptm_iptm(testdir, mock_testclass):
  confidence_file = "POLR2A__POLR2B/POLR2A__POLR2B_summary_confidences.json"
  Path(confidence_file).parent.mkdir()
  shutil.copy(Path(__file__).parent.joinpath(
    "fab53__hvm62_mouse_summary_confidences.json"),
    confidence_file)
  all_lis = [
    af3lis.LIS("POLR2A__POLR2B", "POLR", "POLRB", 0.2, 0.12, 12300, 0.7, 0.3),
    af3lis.LIS("POLR2A__POLR2B", "POLRB", "POLR", 0.2, 0.12, 12300, 0.2, 0.8),
    af3lis.LIS("POLR2A__POLR2C", "POLRB", "POLR", 0.2, 0.12, 12300, 0.9, 0.9),
    af3lis.LIS("POLR2A__POLR2B", "POLRC", "POLR", 0.2, 0.12, 12300, 0.9, 0.9),
  ]
  af3lis.get_sequence_ids = MagicMock(return_value=("POLR", "POLRB"))
  cf, scores = af3lis.get_confidence_scores(confidence_file, ["ptm", "iptm"],
                                            all_lis)
  af3lis.get_sequence_ids.assert_called_once_with(confidence_file, 0, 1)
  assert cf == confidence_file
  assert len(scores) == 2
  assert scores[0] == pytest.approx(0.55)
  assert scores[1] == pytest.approx(0.45)


def test_get_confidence_scores_empty_metrics(testdir, mock_testclass):
  confidence_file = "POLR2A__POLR2B/POLR2A__POLR2B_summary_confidences.json"
  Path(confidence_file).parent.mkdir()
  shutil.copy(Path(__file__).parent.joinpath(
    "fab53__hvm62_mouse_summary_confidences.json"),
    confidence_file)
  all_lis = [
    af3lis.LIS("POLR2A__POLR2B", "POLR", "POLRB", 0.2, 0.12, 12300, 0.76, 0.3),
    af3lis.LIS("POLR2A__POLR2B", "POLRB", "POLR", 0.2, 0.12, 12300, 0.2, 0.8),
    af3lis.LIS("POLR2A__POLR2C", "POLRB", "POLR", 0.2, 0.12, 12300, 0.9, 0.9),
    af3lis.LIS("POLR2A__POLR2B", "POLRC", "POLR", 0.2, 0.12, 12300, 0.9, 0.9),
  ]
  af3lis.get_sequence_ids = MagicMock(return_value=("POLR", "POLRB"))
  cf, scores = af3lis.get_confidence_scores(confidence_file, [], all_lis)
  af3lis.get_sequence_ids.assert_called_once_with(confidence_file, 0, 1)
  assert cf == confidence_file
  assert scores == []


def test_get_confidence_scores_invalid_metrics(testdir, mock_testclass):
  confidence_file = "POLR2A__POLR2B/POLR2A__POLR2B_summary_confidences.json"
  Path(confidence_file).parent.mkdir()
  shutil.copy(Path(__file__).parent.joinpath(
    "fab53__hvm62_mouse_summary_confidences.json"),
    confidence_file)
  all_lis = [
    af3lis.LIS("POLR2A__POLR2B", "POLR", "POLRB", 0.2, 0.12, 12300, 0.76, 0.3),
    af3lis.LIS("POLR2A__POLR2B", "POLRB", "POLR", 0.2, 0.12, 12300, 0.2, 0.8),
    af3lis.LIS("POLR2A__POLR2C", "POLRB", "POLR", 0.2, 0.12, 12300, 0.9, 0.9),
    af3lis.LIS("POLR2A__POLR2B", "POLRC", "POLR", 0.2, 0.12, 12300, 0.9, 0.9),
  ]
  af3lis.get_sequence_ids = MagicMock(return_value=("POLR", "POLRB"))
  with pytest.raises(AssertionError):
    af3lis.get_confidence_scores(confidence_file, ["test"], all_lis)


def test_get_sequence_ids(testdir, mock_testclass):
  confidence_file = "POLR2A__POLR2B/POLR2A__POLR2B_summary_confidences.json"
  Path(confidence_file).parent.mkdir()
  shutil.copy(Path(__file__).parent.joinpath(
    "fab53__hvm62_mouse_summary_confidences.json"),
    confidence_file)
  data_json = Path(confidence_file).parent.joinpath("POLR2A__POLR2B_data.json")
  shutil.copy(Path(__file__).parent.joinpath(
    "ha_h5n1__bmp2_human_data.json"),
    data_json)
  confidences_json = Path(confidence_file).parent.joinpath(
    "POLR2A__POLR2B_confidences.json")
  shutil.copy(Path(__file__).parent.joinpath(
    "ha_h5n1__bmp2_human_confidences.json"),
    confidences_json)
  sequence_one, sequence_two = af3lis.get_sequence_ids(confidence_file, 0, 1)
  assert sequence_one == "BMP"
  assert sequence_two == "HA"
  sequence_one, sequence_two = af3lis.get_sequence_ids(confidence_file, 1, 0)
  assert sequence_one == "HA"
  assert sequence_two == "BMP"


def test_parse_lis(testdir, mock_testclass):
  lis_file = "lis.csv"
  shutil.copy(Path(__file__).parent.joinpath(
    "POLR2A__POLR2B.csv"),
    lis_file)
  all_lis = af3lis.parse_lis(lis_file)
  assert len(all_lis) == 4
  assert all_lis[0].name == "POLR2A__POLR2B"
  assert all_lis[0].chain_i == "POLR"
  assert all_lis[0].chain_j == "POLRB"
  assert all_lis[0].ilis == 0.4505
  assert all_lis[0].lis == 0.3521
  assert all_lis[0].lia == 1436
  assert all_lis[0].iptm == 0.37
  assert all_lis[0].ptm == 0.58
  assert all_lis[1].name == "POLR2A__POLR2B"
  assert all_lis[1].chain_i == "POLRB"
  assert all_lis[1].chain_j == "POLR"
  assert all_lis[1].ilis == 0.0735
  assert all_lis[1].lis == 0.0755
  assert all_lis[1].lia == 1765
  assert all_lis[1].iptm == 0.49
  assert all_lis[1].ptm == 0.61
  assert all_lis[2].name == "POLR2A__POLR2C"
  assert all_lis[2].chain_i == "POLR"
  assert all_lis[2].chain_j == "POLRC"
  assert all_lis[2].ilis == 0.4993
  assert all_lis[2].lis == 0.3996
  assert all_lis[2].lia == 1699
  assert all_lis[2].iptm == 0.31
  assert all_lis[2].ptm == 0.54
  assert all_lis[3].name == "POLR2A__POLR2C"
  assert all_lis[3].chain_i == "POLRC"
  assert all_lis[3].chain_j == "POLR"
  assert all_lis[3].ilis == 0.0546
  assert all_lis[3].lis == 0.0552
  assert all_lis[3].lia == 9510
  assert all_lis[3].iptm == 0.59
  assert all_lis[3].ptm == 0.55


def test_parse_mapping(testdir, mock_testclass):
  mapping_file = "mapping_file.txt"
  with open(mapping_file, "w") as mapping_out:
    mapping_out.write("RPB1_HUMAN\tPOLR2A\n")
    mapping_out.write("NOGENE_HUMAN\t\n")
    mapping_out.write("RPB2_HUMAN\tPOLR2B\n")
  mappings = af3lis.parse_mapping(mapping_file)
  assert "rpb1_human" in mappings
  assert mappings["rpb1_human"] == "POLR2A"
  assert "rpb2_human" in mappings
  assert mappings["rpb2_human"] == "POLR2B"
  assert "nogene_human" not in mappings
  assert "RPB1_HUMAN" not in mappings
  assert "RPB2_HUMAN" not in mappings
  assert "NOGENE_HUMAN" not in mappings


def test_parse_mapping_stdin(testdir, mock_testclass, monkeypatch):
  mapping_file_content = ("RPB1_HUMAN\tPOLR2A\n"
                          "NOGENE_HUMAN\t\n"
                          "RPB2_HUMAN\tPOLR2B\n")
  monkeypatch.setattr("sys.stdin", io.StringIO(mapping_file_content))
  mappings = af3lis.parse_mapping("-")
  assert "rpb1_human" in mappings
  assert mappings["rpb1_human"] == "POLR2A"
  assert "rpb2_human" in mappings
  assert mappings["rpb2_human"] == "POLR2B"
  assert "nogene_human" not in mappings
  assert "RPB1_HUMAN" not in mappings
  assert "RPB2_HUMAN" not in mappings
  assert "NOGENE_HUMAN" not in mappings
