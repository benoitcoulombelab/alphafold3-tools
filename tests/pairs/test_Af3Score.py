import shutil
import io
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pairs import Af3Score, Af3LocalInteractionScore


@pytest.fixture
def mock_testclass():
  _af3_score = Af3Score.af3_score
  _get_confidence_scores = Af3Score.get_confidence_scores
  _parse_mapping = Af3Score.parse_mapping
  _local_interaction_score = Af3LocalInteractionScore.local_interaction_score
  yield
  Af3Score.af3_score = _af3_score
  Af3Score.get_confidence_scores = _get_confidence_scores
  Af3Score.parse_mapping = _parse_mapping
  Af3LocalInteractionScore.local_interaction_score = _local_interaction_score


def test_main(testdir, mock_testclass):
  Af3Score.af3_score = MagicMock()
  Af3Score.main([])
  Af3Score.af3_score.assert_called_once_with(
      input_dir="", output_file="-",
      name=r"([\w-]+)__([\w-]+)_summary_confidences",
      metrics=["iptm"], progress=False,
      mapping_file=None, source_column=0, converted_column=1)


def test_main_parameters(testdir, mock_testclass):
  output = "output.txt"
  metrics = ["iptm", "ranking_score"]
  name = r"(\w+)_(\w+)"
  mapping = "mapping.txt"
  Path(mapping).touch()
  source_column = 2
  converted_column = 3
  Af3Score.af3_score = MagicMock()
  Af3Score.main(
      ["-i", str(testdir), "-o", output, "-m", metrics[0], metrics[1], "-n",
       name, "-p",
       "-M", mapping, "-S", str(source_column + 1), "-C",
       str(converted_column + 1)])
  Af3Score.af3_score.assert_called_once_with(
      input_dir=str(testdir), output_file=output, name=name,
      metrics=metrics, progress=True,
      mapping_file=mapping, source_column=2, converted_column=3)


def test_main_long_parameters(testdir, mock_testclass):
  output = "output.txt"
  metrics = ["iptm", "ranking_score"]
  name = r"(\w+)_(\w+)"
  mapping = "mapping.txt"
  Path(mapping).touch()
  source_column = 2
  converted_column = 3
  Af3Score.af3_score = MagicMock()
  Af3Score.main(
      ["--input", str(testdir), "--output", output, "--metric", metrics[0],
       metrics[1],
       "--name", name, "--progress",
       "--mapping", mapping, "--source_column", str(source_column + 1),
       "--converted_column", str(converted_column + 1)])
  Af3Score.af3_score.assert_called_once_with(
      input_dir=str(testdir), output_file=output, name=name,
      metrics=metrics, progress=True,
      mapping_file=mapping, source_column=2, converted_column=3)


def test_main_no_metrics(testdir, mock_testclass):
  Af3Score.parse_confidence = MagicMock()
  with pytest.raises(SystemExit):
    Af3Score.main(["-m"])
  Af3Score.parse_confidence.assert_not_called()


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
  Af3Score.get_confidence_scores = MagicMock(side_effect=[[0.7772], [0.7601]])
  Af3Score.parse_mapping = MagicMock()
  Af3Score.af3_score(output_file=output)
  Af3Score.get_confidence_scores.assert_any_call(confidence_file_1, ["iptm"])
  Af3Score.get_confidence_scores.assert_any_call(confidence_file_2, ["iptm"])
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
  Af3Score.get_confidence_scores = MagicMock(side_effect=[[0.7772, 0.7059, 0.8952],
                                                          [0.7601, 0.783, 0.8985]])
  Af3Score.parse_mapping = MagicMock(return_value=mappings)
  Af3Score.af3_score("confidences", output,
                     r"([\w-]+)___([\w-]+)_summary_confidences",
                     metrics, False, mappings_file,
                     2, 3)
  Af3Score.get_confidence_scores.assert_any_call(confidence_file_1, metrics)
  Af3Score.get_confidence_scores.assert_any_call(confidence_file_2, metrics)
  Af3Score.parse_mapping.assert_called_once_with(mappings_file, 2, 3)
  with open(output, "r") as output_in:
    assert output_in.readline() == "Bait\tTarget\tipTM\tpTM\tRanking score\n"
    assert output_in.readline() == "POLR2A\tPOLR2B\t0.7772\t0.7059\t0.8952\n"
    assert output_in.readline() == "POLR2A\tPOLR2C\t0.7601\t0.783\t0.8985\n"


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
  Af3Score.get_confidence_scores = MagicMock(side_effect=[[0.7772], [0.7601]])
  Af3Score.parse_mapping = MagicMock()
  with patch("tqdm.tqdm", return_value=confidence_files) as mock_tqdm:
    Af3Score.af3_score(output_file=output,
                       progress=True)
    mock_tqdm.assert_called_once_with(confidence_files)
  Af3Score.get_confidence_scores.assert_any_call(confidence_file_1, ["iptm"])
  Af3Score.get_confidence_scores.assert_any_call(confidence_file_2, ["iptm"])
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
  assert [0.76] == scores


def test_get_confidence_scores_ptm(testdir, mock_testclass):
  confidence_file = "POLR2A__POLR2B/POLR2A__POLR2B_summary_confidences.json"
  Path(confidence_file).parent.mkdir()
  shutil.copy(Path(__file__).parent.joinpath(
      "fab53__hvm62_mouse_summary_confidences.json"),
      confidence_file)
  scores = Af3Score.get_confidence_scores(confidence_file, ["ptm"])
  assert [0.8] == scores


def test_get_confidence_scores_ranking_score(testdir, mock_testclass):
  confidence_file = "POLR2A__POLR2B/POLR2A__POLR2B_summary_confidences.json"
  Path(confidence_file).parent.mkdir()
  shutil.copy(Path(__file__).parent.joinpath(
      "fab53__hvm62_mouse_summary_confidences.json"),
      confidence_file)
  scores = Af3Score.get_confidence_scores(confidence_file, ["ranking_score"])
  assert [0.81] == scores


def test_get_confidence_scores_iptm_ptm_ranking_score(testdir, mock_testclass):
  confidence_file = "POLR2A__POLR2B/POLR2A__POLR2B_summary_confidences.json"
  Path(confidence_file).parent.mkdir()
  shutil.copy(Path(__file__).parent.joinpath(
      "fab53__hvm62_mouse_summary_confidences.json"),
      confidence_file)
  scores = Af3Score.get_confidence_scores(confidence_file, ["iptm", "ptm", "ranking_score"])
  assert [0.76, 0.8, 0.81] == scores


def test_get_confidence_scores_ranking_score_ptm_iptm(testdir, mock_testclass):
  confidence_file = "POLR2A__POLR2B/POLR2A__POLR2B_summary_confidences.json"
  Path(confidence_file).parent.mkdir()
  shutil.copy(Path(__file__).parent.joinpath(
      "fab53__hvm62_mouse_summary_confidences.json"),
      confidence_file)
  scores = Af3Score.get_confidence_scores(confidence_file, ["ranking_score", "ptm", "iptm"])
  assert [0.81, 0.8, 0.76] == scores


def test_get_confidence_scores_empty_metrics(testdir, mock_testclass):
  confidence_file = "POLR2A__POLR2B/POLR2A__POLR2B_summary_confidences.json"
  Path(confidence_file).parent.mkdir()
  shutil.copy(Path(__file__).parent.joinpath(
      "fab53__hvm62_mouse_summary_confidences.json"),
      confidence_file)
  scores = Af3Score.get_confidence_scores(confidence_file, [])
  assert [] == scores


def test_get_confidence_scores_invalid_metrics(testdir, mock_testclass):
  confidence_file = "POLR2A__POLR2B/POLR2A__POLR2B_summary_confidences.json"
  Path(confidence_file).parent.mkdir()
  shutil.copy(Path(__file__).parent.joinpath(
      "fab53__hvm62_mouse_summary_confidences.json"),
      confidence_file)
  with pytest.raises(AssertionError):
    Af3Score.get_confidence_scores(confidence_file, ["test"])


def test_parse_mapping(testdir, mock_testclass):
  mapping_file = "mapping_file.txt"
  with open(mapping_file, 'w') as mapping_out:
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
  monkeypatch.setattr('sys.stdin', io.StringIO(mapping_file_content))
  mappings = Af3Score.parse_mapping("-")
  assert "rpb1_human" in mappings
  assert mappings["rpb1_human"] == "POLR2A"
  assert "rpb2_human" in mappings
  assert mappings["rpb2_human"] == "POLR2B"
  assert "nogene_human" not in mappings
  assert "RPB1_HUMAN" not in mappings
  assert "RPB2_HUMAN" not in mappings
  assert "NOGENE_HUMAN" not in mappings
