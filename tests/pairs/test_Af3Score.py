import concurrent.futures
import shutil
import io
import os
import statistics
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pairs import Af3Score, Af3LocalInteractionScore


@pytest.fixture
def mock_testclass():
  _af3_score = Af3Score.af3_score
  _get_confidence_scores = Af3Score.get_confidence_scores
  _get_sequence_index = Af3Score.get_sequence_index
  _parse_mapping = Af3Score.parse_mapping
  _local_interaction_score = Af3LocalInteractionScore.local_interaction_score
  yield
  Af3Score.af3_score = _af3_score
  Af3Score.get_confidence_scores = _get_confidence_scores
  Af3Score.get_sequence_index = _get_sequence_index
  Af3Score.parse_mapping = _parse_mapping
  Af3LocalInteractionScore.local_interaction_score = _local_interaction_score


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
  Af3Score.af3_score = MagicMock()
  Af3Score.main([])
  Af3Score.af3_score.assert_called_once_with(
      input_dir="", output_file="-",
      name=r"([\w-]+)__([\w-]+)_summary_confidences",
      metrics=["iptm"],
      sequence_one=0, sequence_two=1,
      progress=False,
      mapping_file=None, source_column=0, converted_column=1, threads=1)


def test_main_parameters(testdir, mock_testclass):
  output = "output.txt"
  metrics = ["iptm", "ranking_score"]
  name = r"(\w+)_(\w+)"
  mapping = "mapping.txt"
  Path(mapping).touch()
  sequence_one = 2
  sequence_two = 3
  source_column = 2
  converted_column = 3
  threads = 2
  Af3Score.af3_score = MagicMock()
  Af3Score.main(
      ["-i", str(testdir), "-o", output, "-m", metrics[0], metrics[1], "-n",
       name, "-1", str(sequence_one), "-2", str(sequence_two), "-p",
       "-M", mapping, "-S", str(source_column + 1), "-C",
       str(converted_column + 1), "-t", str(threads)])
  Af3Score.af3_score.assert_called_once_with(
      input_dir=str(testdir), output_file=output, name=name,
      metrics=metrics,
      sequence_one=sequence_one - 1, sequence_two=sequence_two - 1,
      progress=True,
      mapping_file=mapping, source_column=source_column, converted_column=converted_column,
      threads=threads)


def test_main_long_parameters(testdir, mock_testclass):
  output = "output.txt"
  metrics = ["iptm", "ranking_score"]
  name = r"(\w+)_(\w+)"
  mapping = "mapping.txt"
  Path(mapping).touch()
  sequence_one = 2
  sequence_two = 3
  source_column = 2
  converted_column = 3
  threads = 2
  Af3Score.af3_score = MagicMock()
  Af3Score.main(
      ["--input", str(testdir), "--output", output, "--metric", metrics[0],
       metrics[1],
       "--name", name, "--sequence1", str(sequence_one), "--sequence2", str(sequence_two), "--progress",
       "--mapping", mapping, "--source_column", str(source_column + 1),
       "--converted_column", str(converted_column + 1), "--threads", str(threads)])
  Af3Score.af3_score.assert_called_once_with(
      input_dir=str(testdir), output_file=output, name=name,
      metrics=metrics,
      sequence_one=sequence_one - 1, sequence_two=sequence_two - 1,
      progress=True,
      mapping_file=mapping, source_column=source_column, converted_column=converted_column,
      threads=threads)


def test_main_no_metrics(testdir, mock_testclass):
  Af3Score.af3_score = MagicMock()
  with pytest.raises(SystemExit):
    Af3Score.main(["-m"])
  Af3Score.af3_score.assert_not_called()


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
  Af3Score.get_sequence_index = MagicMock(side_effect=[[0, 1], [3, 2]])
  Af3Score.get_confidence_scores = MagicMock(side_effect=[[0.7772], [0.7601]])
  Af3Score.parse_mapping = MagicMock()
  executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
  with patch("concurrent.futures.ProcessPoolExecutor", return_value=executor):
    Af3Score.af3_score(output_file=output)
  Af3Score.get_sequence_index.assert_any_call(confidence_file_1, 0, 1)
  Af3Score.get_sequence_index.assert_any_call(confidence_file_2, 0, 1)
  Af3Score.get_confidence_scores.assert_any_call(confidence_file_1, ["iptm"], 0, 1)
  Af3Score.get_confidence_scores.assert_any_call(confidence_file_2, ["iptm"], 3, 2)
  Af3Score.parse_mapping.assert_not_called()
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
  metrics = ["iptm", "ptm", "ranking_score"]
  mappings_file = "mappings.txt"
  Path(mappings_file).touch()
  mappings = {"RPB-1": "POLR2A", "RPB-2": "POLR2B", "RPB-3": "POLR2C"}
  Af3Score.get_sequence_index = MagicMock(side_effect=[[0, 1], [3, 2]])
  Af3Score.get_confidence_scores = MagicMock(side_effect=[[0.7772, 0.7059, 0.8952],
                                                          [0.7601, 0.783, 0.8985]])
  Af3Score.parse_mapping = MagicMock(return_value=mappings)
  executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
  with patch("concurrent.futures.ProcessPoolExecutor", return_value=executor):
    Af3Score.af3_score("confidences", output,
                       r"([\w-]+)___([\w-]+)_summary_confidences",
                       metrics, 1, 2, False, mappings_file,
                       2, 3)
  Af3Score.get_sequence_index.assert_any_call(confidence_file_1, 1, 2)
  Af3Score.get_sequence_index.assert_any_call(confidence_file_2, 1, 2)
  Af3Score.get_confidence_scores.assert_any_call(confidence_file_1, metrics, 0, 1)
  Af3Score.get_confidence_scores.assert_any_call(confidence_file_2, metrics, 3, 2)
  Af3Score.parse_mapping.assert_called_once_with(mappings_file, 2, 3)
  with open(output, "r") as output_in:
    assert output_in.readline() == "Bait\tTarget\tipTM\tpTM\tRanking score\n"
    assert output_in.readline() == "POLR2A\tPOLR2B\t0.7772\t0.7059\t0.8952\n"
    assert output_in.readline() == "POLR2A\tPOLR2C\t0.7601\t0.783\t0.8985\n"


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
  metrics = ["iptm", "ptm", "ranking_score"]
  mappings_file = "mappings.txt"
  Path(mappings_file).touch()
  mappings = {"RPB-1": "POLR2A", "RPB-2": "POLR2B", "RPB-3": "POLR2C"}
  Af3Score.get_sequence_index = MagicMock(side_effect=[[0, 1], [3, 2]])
  Af3Score.get_confidence_scores = MagicMock(side_effect=[[0.7772, 0.7059, 0.8952],
                                                          AssertionError("error on second call")])
  Af3Score.parse_mapping = MagicMock(return_value=mappings)
  executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
  with patch("concurrent.futures.ProcessPoolExecutor", return_value=executor):
    with pytest.raises(AssertionError):
      Af3Score.af3_score("confidences", output,
                       r"([\w-]+)___([\w-]+)_summary_confidences",
                       metrics, 1, 2, False, mappings_file,
                       2, 3)
  Af3Score.get_sequence_index.assert_any_call(confidence_file_1, 1, 2)
  Af3Score.get_sequence_index.assert_any_call(confidence_file_2, 1, 2)
  Af3Score.get_confidence_scores.assert_any_call(confidence_file_1, metrics, 0, 1)
  Af3Score.get_confidence_scores.assert_any_call(confidence_file_2, metrics, 3, 2)
  Af3Score.parse_mapping.assert_called_once_with(mappings_file, 2, 3)


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
  Af3Score.get_sequence_index = MagicMock(side_effect=[[0, 1], [3, 2]])
  Af3Score.get_confidence_scores = MagicMock(side_effect=[[0.7772], [0.7601]])
  Af3Score.parse_mapping = MagicMock()
  tqdm_list = MagicMock()
  with patch("tqdm.tqdm", return_value=tqdm_list) as mock_tqdm:
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    with patch("concurrent.futures.ProcessPoolExecutor", return_value=executor):
      Af3Score.af3_score(output_file=output,
                         progress=True)
    mock_tqdm.assert_called_once_with(total=len(confidence_files))
    assert tqdm_list.__enter__().update.call_count == 2
    tqdm_list.__enter__().update.assert_any_call(1)
  Af3Score.get_sequence_index.assert_any_call(confidence_file_1, 0, 1)
  Af3Score.get_sequence_index.assert_any_call(confidence_file_2, 0, 1)
  Af3Score.get_confidence_scores.assert_any_call(confidence_file_1, ["iptm"], 0, 1)
  Af3Score.get_confidence_scores.assert_any_call(confidence_file_2, ["iptm"], 3, 2)
  Af3Score.parse_mapping.assert_not_called()
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
  Af3Score.get_confidence_scores = MagicMock(side_effect=[[0.7772], [0.7601]])
  Af3Score.parse_mapping = MagicMock()
  with pytest.raises(AssertionError):
    Af3Score.af3_score(output_file=output,
                       metrics=[])
  Af3Score.get_confidence_scores.assert_not_called()
  Af3Score.parse_mapping.assert_not_called()


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
  Af3Score.get_confidence_scores = MagicMock(side_effect=[[0.7772], [0.7601]])
  Af3Score.parse_mapping = MagicMock()
  with pytest.raises(AssertionError):
    Af3Score.af3_score(output_file=output,
                       metrics=["test"])
  Af3Score.get_confidence_scores.assert_not_called()
  Af3Score.parse_mapping.assert_not_called()


def test_get_confidence_scores_iptm(testdir, mock_testclass):
  confidence_file = "POLR2A__POLR2B/POLR2A__POLR2B_summary_confidences.json"
  Path(confidence_file).parent.mkdir()
  shutil.copy(Path(__file__).parent.joinpath(
      "fab53__hvm62_mouse_summary_confidences.json"),
      confidence_file)
  scores = Af3Score.get_confidence_scores(confidence_file, ["iptm"])
  assert scores == [0.76]


def test_get_confidence_scores_ptm(testdir, mock_testclass):
  confidence_file = "POLR2A__POLR2B/POLR2A__POLR2B_summary_confidences.json"
  Path(confidence_file).parent.mkdir()
  shutil.copy(Path(__file__).parent.joinpath(
      "fab53__hvm62_mouse_summary_confidences.json"),
      confidence_file)
  scores = Af3Score.get_confidence_scores(confidence_file, ["ptm"])
  assert scores == [0.8]


def test_get_confidence_scores_ranking_score(testdir, mock_testclass):
  confidence_file = "POLR2A__POLR2B/POLR2A__POLR2B_summary_confidences.json"
  Path(confidence_file).parent.mkdir()
  shutil.copy(Path(__file__).parent.joinpath(
      "fab53__hvm62_mouse_summary_confidences.json"),
      confidence_file)
  scores = Af3Score.get_confidence_scores(confidence_file, ["ranking_score"])
  assert scores == [0.81]


def test_get_confidence_scores_lis(testdir, mock_testclass):
  confidence_file = "POLR2A__POLR2B/POLR2A__POLR2B_summary_confidences.json"
  Path(confidence_file).parent.mkdir()
  create_alphafold3_files("POLR2A__POLR2B", "POLR2A__POLR2B")
  shutil.copy(Path(__file__).parent.joinpath(
      "fab53__hvm62_mouse_summary_confidences.json"),
      confidence_file)
  lis_scores = [
    [0.322131832, 0.210386822, 16614], [0.15153642, 0.088703528, 6339], [0.301954094, 0.175839958, 27422],
    [0.247117775, 0.176551479, 5151], [0.178270958, 0.110770328, 5608]]
  Af3LocalInteractionScore.local_interaction_score = MagicMock(side_effect=lis_scores)
  scores = Af3Score.get_confidence_scores(confidence_file, ["lis"])
  Af3LocalInteractionScore.local_interaction_score.assert_any_call(
      "POLR2A__POLR2B/seed-1_sample-0/confidences.json", "POLR2A__POLR2B/seed-1_sample-0/model.cif", subunit_one=0, subunit_two=1)
  Af3LocalInteractionScore.local_interaction_score.assert_any_call(
      "POLR2A__POLR2B/seed-1_sample-1/confidences.json", "POLR2A__POLR2B/seed-1_sample-1/model.cif", subunit_one=0, subunit_two=1)
  Af3LocalInteractionScore.local_interaction_score.assert_any_call(
      "POLR2A__POLR2B/seed-1_sample-2/confidences.json", "POLR2A__POLR2B/seed-1_sample-2/model.cif", subunit_one=0, subunit_two=1)
  Af3LocalInteractionScore.local_interaction_score.assert_any_call(
      "POLR2A__POLR2B/seed-1_sample-3/confidences.json", "POLR2A__POLR2B/seed-1_sample-3/model.cif", subunit_one=0, subunit_two=1)
  Af3LocalInteractionScore.local_interaction_score.assert_any_call(
      "POLR2A__POLR2B/seed-1_sample-4/confidences.json", "POLR2A__POLR2B/seed-1_sample-4/model.cif", subunit_one=0, subunit_two=1)
  assert scores[0] == pytest.approx(statistics.mean(s[0] for s in lis_scores))
  assert scores[1] == pytest.approx(statistics.mean(s[1] for s in lis_scores))
  assert scores[2] == pytest.approx(statistics.mean(s[2] for s in lis_scores))


def test_get_confidence_scores_best_lis(testdir, mock_testclass):
  confidence_file = "POLR2A__POLR2B/POLR2A__POLR2B_summary_confidences.json"
  Path(confidence_file).parent.mkdir()
  create_alphafold3_files("POLR2A__POLR2B", "POLR2A__POLR2B")
  shutil.copy(Path(__file__).parent.joinpath(
      "fab53__hvm62_mouse_summary_confidences.json"),
      confidence_file)
  Af3LocalInteractionScore.local_interaction_score = MagicMock(return_value=[0.322131832, 0.210386822, 16614])
  scores = Af3Score.get_confidence_scores(confidence_file, ["best_lis"])
  Af3LocalInteractionScore.local_interaction_score.assert_called_once_with(
      "POLR2A__POLR2B/POLR2A__POLR2B_confidences.json", "POLR2A__POLR2B/POLR2A__POLR2B_model.cif", subunit_one=0, subunit_two=1)
  assert scores == [0.322131832, 0.210386822, 16614]


def test_get_confidence_scores_iptm_ptm_ranking_score(testdir, mock_testclass):
  confidence_file = "POLR2A__POLR2B/POLR2A__POLR2B_summary_confidences.json"
  Path(confidence_file).parent.mkdir()
  shutil.copy(Path(__file__).parent.joinpath(
      "fab53__hvm62_mouse_summary_confidences.json"),
      confidence_file)
  scores = Af3Score.get_confidence_scores(confidence_file, ["iptm", "ptm", "ranking_score"])
  assert scores == [0.76, 0.8, 0.81]


def test_get_confidence_scores_ranking_score_ptm_iptm(testdir, mock_testclass):
  confidence_file = "POLR2A__POLR2B/POLR2A__POLR2B_summary_confidences.json"
  Path(confidence_file).parent.mkdir()
  shutil.copy(Path(__file__).parent.joinpath(
      "fab53__hvm62_mouse_summary_confidences.json"),
      confidence_file)
  scores = Af3Score.get_confidence_scores(confidence_file, ["ranking_score", "ptm", "iptm"])
  assert scores == [0.81, 0.8, 0.76]


def test_get_confidence_scores_empty_metrics(testdir, mock_testclass):
  confidence_file = "POLR2A__POLR2B/POLR2A__POLR2B_summary_confidences.json"
  Path(confidence_file).parent.mkdir()
  shutil.copy(Path(__file__).parent.joinpath(
      "fab53__hvm62_mouse_summary_confidences.json"),
      confidence_file)
  scores = Af3Score.get_confidence_scores(confidence_file, [])
  assert scores == []


def test_get_confidence_scores_invalid_metrics(testdir, mock_testclass):
  confidence_file = "POLR2A__POLR2B/POLR2A__POLR2B_summary_confidences.json"
  Path(confidence_file).parent.mkdir()
  shutil.copy(Path(__file__).parent.joinpath(
      "fab53__hvm62_mouse_summary_confidences.json"),
      confidence_file)
  with pytest.raises(AssertionError):
    Af3Score.get_confidence_scores(confidence_file, ["test"])


def test_get_sequence_index(testdir, mock_testclass):
  confidence_file = "POLR2A__POLR2B/POLR2A__POLR2B_summary_confidences.json"
  Path(confidence_file).parent.mkdir()
  shutil.copy(Path(__file__).parent.joinpath(
      "fab53__hvm62_mouse_summary_confidences.json"),
      confidence_file)
  data_json = Path(confidence_file).parent.joinpath("POLR2A__POLR2B_data.json")
  shutil.copy(Path(__file__).parent.joinpath(
      "ha_h5n1__bmp2_human_data.json"),
      data_json)
  confidences_json = Path(confidence_file).parent.joinpath("POLR2A__POLR2B_confidences.json")
  shutil.copy(Path(__file__).parent.joinpath(
      "ha_h5n1__bmp2_human_confidences.json"),
      confidences_json)
  sequence_one, sequence_two = Af3Score.get_sequence_index(confidence_file, 0, 1)
  assert sequence_one == 1
  assert sequence_two == 0
  sequence_one, sequence_two = Af3Score.get_sequence_index(confidence_file, 1, 0)
  assert sequence_one == 0
  assert sequence_two == 1


def test_parse_mapping(testdir, mock_testclass):
  mapping_file = "mapping_file.txt"
  with open(mapping_file, "w") as mapping_out:
    mapping_out.write("RPB1_HUMAN\tPOLR2A\n")
    mapping_out.write("NOGENE_HUMAN\t\n")
    mapping_out.write("RPB2_HUMAN\tPOLR2B\n")
  mappings = Af3Score.parse_mapping(mapping_file)
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
  mappings = Af3Score.parse_mapping("-")
  assert "rpb1_human" in mappings
  assert mappings["rpb1_human"] == "POLR2A"
  assert "rpb2_human" in mappings
  assert mappings["rpb2_human"] == "POLR2B"
  assert "nogene_human" not in mappings
  assert "RPB1_HUMAN" not in mappings
  assert "RPB2_HUMAN" not in mappings
  assert "NOGENE_HUMAN" not in mappings
