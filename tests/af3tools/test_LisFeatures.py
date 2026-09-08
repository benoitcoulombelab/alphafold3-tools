import contextlib
import io
import os
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from af3tools import LisFeatures


@pytest.fixture
def mock_testclass():
  _add_bait_target = LisFeatures.add_bait_target
  _get_bait_target = LisFeatures.get_bait_target
  _get_sequence_ids = LisFeatures.get_sequence_ids
  _parse_lis = LisFeatures.parse_lis
  _load_json = LisFeatures.load_json
  yield
  LisFeatures.add_bait_target = _add_bait_target
  LisFeatures.get_bait_target = _get_bait_target
  LisFeatures.get_sequence_ids = _get_sequence_ids
  LisFeatures.parse_lis = _parse_lis
  LisFeatures.load_json = _load_json


@contextlib.contextmanager
def uncloseable(fd):
  """
  Context manager which turns the fd's close operation to no-op for the duration of the context.
  """
  close = fd.close
  fd.close = lambda: None
  yield fd
  fd.close = close


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
  LisFeatures.add_bait_target = MagicMock()
  LisFeatures.main([])
  LisFeatures.add_bait_target.assert_called_once_with(
    lis_file=lis_file,
    alphafold_dir="structures",
    output_file="-",
    progress=False)


def test_main_parameters(testdir, mock_testclass):
  lis_file = "lis.csv"
  Path(lis_file).touch()
  alphafold_dir = "alphafold_dir"
  Path(alphafold_dir).mkdir()
  output = "output.txt"
  LisFeatures.add_bait_target = MagicMock()
  LisFeatures.main(
    ["-l", str(lis_file), "-a", alphafold_dir, "-o", output, "-p"])
  LisFeatures.add_bait_target.assert_called_once_with(
    lis_file=lis_file,
    alphafold_dir=alphafold_dir,
    output_file=output,
    progress=True)


def test_main_long_parameters(testdir, mock_testclass):
  lis_file = "lis.csv"
  Path(lis_file).touch()
  alphafold_dir = "alphafold_dir"
  Path(alphafold_dir).mkdir()
  output = "output.txt"
  LisFeatures.add_bait_target = MagicMock()
  LisFeatures.main(
    ["--lis", str(lis_file), "--alphafold", alphafold_dir, "--output", output,
     "--progress"])
  LisFeatures.add_bait_target.assert_called_once_with(
    lis_file=lis_file,
    alphafold_dir=alphafold_dir,
    output_file=output,
    progress=True)


def test_add_bait_target(testdir, mock_testclass):
  lis_file = "structures/structures_lis_analysis.csv"
  alphafold_dir = "structures"
  Path(lis_file).parent.mkdir()
  shutil.copy(Path(__file__).parent.joinpath("lis_ouput.csv"), lis_file)
  lis_entries = [
    {"name": "HA_H5N1__BMP2_HUMAN__DMSO", "rank": "1945201344_0", "model": "",
     "chain_i": "HA", "chain_j": "BMP", "iLIS": "0.59"},
    {"name": "HA_H5N1__BMP2_HUMAN__DMSO", "rank": "1945201344_3", "model": "",
     "chain_i": "HA", "chain_j": "DMSO", "iLIS": "0.50"},
    {"name": "HA_H5N1__BMP2_HUMAN__DMSO", "rank": "1945201344_2", "model": "",
     "chain_i": "BMP", "chain_j": "DMSO", "iLIS": "0.29"},
  ]
  LisFeatures.parse_lis = MagicMock(side_effect=[lis_entries])
  LisFeatures.get_bait_target = MagicMock(
    side_effect=[("POLR2A", "POLR2B"), ("POLR2A", "POLR2C"),
                 ("POLR2B", "POLR2C")])
  output_buffer = io.StringIO()
  with uncloseable(output_buffer), patch("sys.stdout", new=output_buffer):
    LisFeatures.add_bait_target()
  LisFeatures.parse_lis.assert_called_once_with(lis_file)
  LisFeatures.get_bait_target.assert_any_call(lis_entries[0], alphafold_dir)
  LisFeatures.get_bait_target.assert_any_call(lis_entries[1], alphafold_dir)
  LisFeatures.get_bait_target.assert_any_call(lis_entries[2], alphafold_dir)
  output_lines = output_buffer.getvalue().rstrip("\r\n").split("\n")
  output_lines = [output_line.rstrip("\r\n") for output_line in output_lines]
  assert output_lines[0] == "bait,target,name,rank,model,chain_i,chain_j,iLIS"
  assert output_lines[
           1] == "POLR2A,POLR2B,HA_H5N1__BMP2_HUMAN__DMSO,1945201344_0,,HA,BMP,0.59"
  assert output_lines[
           2] == "POLR2A,POLR2C,HA_H5N1__BMP2_HUMAN__DMSO,1945201344_3,,HA,DMSO,0.50"
  assert output_lines[
           3] == "POLR2B,POLR2C,HA_H5N1__BMP2_HUMAN__DMSO,1945201344_2,,BMP,DMSO,0.29"


def test_add_bait_target_parameters(testdir, mock_testclass):
  lis_file = "lis.csv"
  shutil.copy(Path(__file__).parent.joinpath("lis_ouput.csv"), lis_file)
  alphafold_dir = "alphafold_dir"
  Path(alphafold_dir).mkdir()
  output = "output.txt"
  lis_entries = [
    {"name": "HA_H5N1__BMP2_HUMAN__DMSO", "rank": "1945201344_0", "model": "",
     "chain_i": "HA", "chain_j": "BMP", "iLIS": "0.59"},
    {"name": "HA_H5N1__BMP2_HUMAN__DMSO", "rank": "1945201344_3", "model": "",
     "chain_i": "HA", "chain_j": "DMSO", "iLIS": "0.50"},
    {"name": "HA_H5N1__BMP2_HUMAN__DMSO", "rank": "1945201344_2", "model": "",
     "chain_i": "BMP", "chain_j": "DMSO", "iLIS": "0.29"},
  ]
  LisFeatures.parse_lis = MagicMock(side_effect=[lis_entries])
  LisFeatures.get_bait_target = MagicMock(
    side_effect=[("POLR2A", "POLR2B"), ("POLR2A", "POLR2C"),
                 ("POLR2B", "POLR2C")])
  LisFeatures.add_bait_target(lis_file=lis_file, alphafold_dir=alphafold_dir,
                              output_file=output)
  LisFeatures.parse_lis.assert_called_once_with(lis_file)
  LisFeatures.get_bait_target.assert_any_call(lis_entries[0], alphafold_dir)
  LisFeatures.get_bait_target.assert_any_call(lis_entries[1], alphafold_dir)
  LisFeatures.get_bait_target.assert_any_call(lis_entries[2], alphafold_dir)
  with open(output, "r") as output_in:
    assert output_in.readline() == "bait,target,name,rank,model,chain_i,chain_j,iLIS\n"
    assert output_in.readline() == "POLR2A,POLR2B,HA_H5N1__BMP2_HUMAN__DMSO,1945201344_0,,HA,BMP,0.59\n"
    assert output_in.readline() == "POLR2A,POLR2C,HA_H5N1__BMP2_HUMAN__DMSO,1945201344_3,,HA,DMSO,0.50\n"
    assert output_in.readline() == "POLR2B,POLR2C,HA_H5N1__BMP2_HUMAN__DMSO,1945201344_2,,BMP,DMSO,0.29\n"


def test_add_bait_target_failure(testdir, mock_testclass):
  lis_file = "lis.csv"
  shutil.copy(Path(__file__).parent.joinpath("lis_ouput.csv"), lis_file)
  alphafold_dir = "alphafold_dir"
  Path(alphafold_dir).mkdir()
  output = "output.txt"
  lis_entries = [
    {"name": "HA_H5N1__BMP2_HUMAN__DMSO", "rank": "1945201344_0", "model": "",
     "chain_i": "HA", "chain_j": "BMP", "iLIS": "0.59"},
    {"name": "HA_H5N1__BMP2_HUMAN__DMSO", "rank": "1945201344_3", "model": "",
     "chain_i": "HA", "chain_j": "DMSO", "iLIS": "0.50"},
    {"name": "HA_H5N1__BMP2_HUMAN__DMSO", "rank": "1945201344_2", "model": "",
     "chain_i": "BMP", "chain_j": "DMSO", "iLIS": "0.29"},
  ]
  LisFeatures.parse_lis = MagicMock(side_effect=[lis_entries])
  LisFeatures.get_bait_target = MagicMock(
    side_effect=[("POLR2A", "POLR2B"), AssertionError("error on second call"),
                 ("POLR2B", "POLR2C")])
  with pytest.raises(AssertionError):
    LisFeatures.add_bait_target(lis_file=lis_file, alphafold_dir=alphafold_dir,
                                output_file=output)
  assert not os.path.isfile(output)


def test_add_bait_target_progress(testdir, mock_testclass):
  lis_file = "lis.csv"
  shutil.copy(Path(__file__).parent.joinpath("lis_ouput.csv"), lis_file)
  alphafold_dir = "alphafold_dir"
  Path(alphafold_dir).mkdir()
  output = "output.txt"
  lis_entries = [
    {"name": "HA_H5N1__BMP2_HUMAN__DMSO", "rank": "1945201344_0", "model": "",
     "chain_i": "HA", "chain_j": "BMP", "iLIS": "0.59"},
    {"name": "HA_H5N1__BMP2_HUMAN__DMSO", "rank": "1945201344_3", "model": "",
     "chain_i": "HA", "chain_j": "DMSO", "iLIS": "0.50"},
    {"name": "HA_H5N1__BMP2_HUMAN__DMSO", "rank": "1945201344_2", "model": "",
     "chain_i": "BMP", "chain_j": "DMSO", "iLIS": "0.29"},
  ]
  LisFeatures.parse_lis = MagicMock(side_effect=[lis_entries])
  LisFeatures.get_bait_target = MagicMock(
    side_effect=[("POLR2A", "POLR2B"), ("POLR2A", "POLR2C"),
                 ("POLR2B", "POLR2C")])
  tqdm_list = lis_entries
  with patch("tqdm.tqdm", return_value=tqdm_list) as mock_tqdm:
    LisFeatures.add_bait_target(lis_file=lis_file, alphafold_dir=alphafold_dir,
                                output_file=output, progress=True)
    mock_tqdm.assert_called_once_with(lis_entries)
  LisFeatures.parse_lis.assert_called_once_with(lis_file)
  LisFeatures.get_bait_target.assert_any_call(lis_entries[0], alphafold_dir)
  LisFeatures.get_bait_target.assert_any_call(lis_entries[1], alphafold_dir)
  LisFeatures.get_bait_target.assert_any_call(lis_entries[2], alphafold_dir)
  with open(output, "r") as output_in:
    assert output_in.readline() == "bait,target,name,rank,model,chain_i,chain_j,iLIS\n"
    assert output_in.readline() == "POLR2A,POLR2B,HA_H5N1__BMP2_HUMAN__DMSO,1945201344_0,,HA,BMP,0.59\n"
    assert output_in.readline() == "POLR2A,POLR2C,HA_H5N1__BMP2_HUMAN__DMSO,1945201344_3,,HA,DMSO,0.50\n"
    assert output_in.readline() == "POLR2B,POLR2C,HA_H5N1__BMP2_HUMAN__DMSO,1945201344_2,,BMP,DMSO,0.29\n"


def test_get_bait_target(testdir, mock_testclass):
  lis_entry = {"name": "HA_H5N1__BMP2_HUMAN__DMSO", "rank": "1945201344_0",
               "model": "",
               "chain_i": "HA", "chain_j": "BMP", "iLIS": "0.59"}
  alphafold_dir = "structures"
  Path(alphafold_dir).mkdir()
  data_file = os.path.join(alphafold_dir,
                           "HA_H5N1__BMP2_HUMAN__DMSO/HA_H5N1__BMP2_HUMAN__DMSO_data.json")
  Path(data_file).parent.mkdir()
  Path(data_file).touch()
  sequence_ids = ["HA", "BMP", "DMSO"]
  LisFeatures.get_sequence_ids = MagicMock(side_effect=[sequence_ids])
  bait, target = LisFeatures.get_bait_target(lis_entry,
                                             alphafold_dir=alphafold_dir)
  LisFeatures.get_sequence_ids.assert_called_once_with(data_file)
  assert bait == "HA_H5N1"
  assert target == "BMP2_HUMAN"


def test_get_bait_target_reversechains(testdir, mock_testclass):
  lis_entry = {"name": "HA_H5N1__BMP2_HUMAN__DMSO", "rank": "1945201344_0",
               "model": "",
               "chain_i": "BMP", "chain_j": "HA", "iLIS": "0.59"}
  alphafold_dir = "structures"
  Path(alphafold_dir).mkdir()
  data_file = os.path.join(alphafold_dir,
                           "HA_H5N1__BMP2_HUMAN__DMSO/HA_H5N1__BMP2_HUMAN__DMSO_data.json")
  Path(data_file).parent.mkdir()
  Path(data_file).touch()
  sequence_ids = ["HA", "BMP", "DMSO"]
  LisFeatures.get_sequence_ids = MagicMock(side_effect=[sequence_ids])
  bait, target = LisFeatures.get_bait_target(lis_entry,
                                             alphafold_dir=alphafold_dir)
  LisFeatures.get_sequence_ids.assert_called_once_with(data_file)
  assert bait == "HA_H5N1"
  assert target == "BMP2_HUMAN"


def test_get_bait_target_missingdatafile(testdir, mock_testclass):
  lis_entry = {"name": "HA_H5N1__BMP2_HUMAN__DMSO", "rank": "1945201344_0",
               "model": "",
               "chain_i": "HA", "chain_j": "BMP", "iLIS": "0.59"}
  alphafold_dir = "structures"
  Path(alphafold_dir).mkdir()
  data_file = os.path.join(alphafold_dir,
                           "HA_H5N1__BMP2_HUMAN__DMSO/HA_H5N1__BMP2_HUMAN__DMSO_data.json")
  Path(data_file).parent.mkdir()
  sequence_ids = ["HA", "BMP", "DMSO"]
  LisFeatures.get_sequence_ids = MagicMock(side_effect=[sequence_ids])
  with pytest.raises(FileNotFoundError):
    LisFeatures.get_bait_target(lis_entry,
                                alphafold_dir=alphafold_dir)


def test_get_sequence_ids(testdir, mock_testclass):
  alphafold_dir = "structures"
  Path(alphafold_dir).mkdir()
  data_file = os.path.join(alphafold_dir,
                           "HA_H5N1__BMP2_HUMAN__DMSO/HA_H5N1__BMP2_HUMAN__DMSO_data.json")
  Path(data_file).parent.mkdir()
  shutil.copy(
    Path(__file__).parent.joinpath("ha_h5n1__bmp2_human__dmso_data.json"),
    data_file)
  sequence_ids = LisFeatures.get_sequence_ids(data_file)
  assert sequence_ids == ["BMP", "HA", "DMSO"]


def test_parse_lis(testdir, mock_testclass):
  lis_file = "lis.csv"
  shutil.copy(Path(__file__).parent.joinpath("lis_ouput.csv"), lis_file)
  lis_entries = LisFeatures.parse_lis(lis_file)
  assert len(lis_entries) == 5
  assert lis_entries[0]["name"] == "HA_H5N1__BMP2_HUMAN__DMSO"
  assert lis_entries[0]["rank"] == "1945201344_0"
  assert lis_entries[0]["model"] == ""
  assert lis_entries[0]["chain_i"] == "HA"
  assert lis_entries[0]["chain_j"] == "BMP"
  assert lis_entries[0]["iLIS"] == "0.5401"
  assert lis_entries[0]["iLIA"] == "325.9"
  assert lis_entries[0]["iLISA"] == "176"
  assert lis_entries[0]["ipSAE"] == "0.0982"
  assert lis_entries[0]["actifpTM"] == "0.9562"
  assert lis_entries[0]["LIS"] == "0.4344"
  assert lis_entries[0]["cLIS"] == "0.6715"
  assert lis_entries[0]["LIA"] == "1713"
  assert lis_entries[0]["cLIA"] == "62"
  assert lis_entries[0]["ipTM"] == "0.32"
  assert lis_entries[0]["pLDDT_i"] == "86.4"
  assert lis_entries[0]["pLDDT_j"] == "81.3"
  assert lis_entries[0]["pLDDT"] == "83.2"
  assert lis_entries[0]["pTM"] == "0.55"
  assert lis_entries[0]["LIR_i"] == "39"
  assert lis_entries[0]["LIR_j"] == "32"
  assert lis_entries[0]["cLIR_i"] == "13"
  assert lis_entries[0]["cLIR_j"] == "12"
  assert lis_entries[0]["LIpLDDT_i"] == "72.5"
  assert lis_entries[0]["LIpLDDT_j"] == "73.2"
  assert lis_entries[0]["LIpLDDT"] == "72.8"
  assert lis_entries[0]["cLIpLDDT_i"] == "78.3"
  assert lis_entries[0]["cLIpLDDT_j"] == "78.9"
  assert lis_entries[0]["cLIpLDDT"] == "78.6"
  assert lis_entries[0]["len_i"] == "770"
  assert lis_entries[0]["len_j"] == "1269"
  assert lis_entries[0]["LIR_indices_i"] == "[59-96,98]"
  assert lis_entries[0]["LIR_indices_j"] == "[1205-1236]"
  assert lis_entries[0][
           "cLIR_indices_i"] == "[66,69,72-73,76-77,79-80,83-84,86-87,90]"
  assert lis_entries[0][
           "cLIR_indices_j"] == "[1211,1214-1215,1217-1218,1221-1222,1224-1225,1228-1229,1232]"
  assert lis_entries[0][
           "structure_file"] == "SPIKE_JN1__ECE1_HUMAN__CBD_seed-1945201344_sample-0_model.cif"
  assert lis_entries[1]["name"] == "HA_H5N1__BMP2_HUMAN__DMSO"
  assert lis_entries[1]["rank"] == "1945201344_3"
  assert lis_entries[1]["model"] == ""
  assert lis_entries[1]["chain_i"] == "HA"
  assert lis_entries[1]["chain_j"] == "DMSO"
  assert lis_entries[1]["iLIS"] == "0.5316"
  assert lis_entries[1]["iLIA"] == "315.8"
  assert lis_entries[1]["iLISA"] == "167.9"
  assert lis_entries[1]["ipSAE"] == "0.0991"
  assert lis_entries[1]["actifpTM"] == "0.9519"
  assert lis_entries[1]["LIS"] == "0.4275"
  assert lis_entries[1]["cLIS"] == "0.6611"
  assert lis_entries[1]["LIA"] == "1720"
  assert lis_entries[1]["cLIA"] == "58"
  assert lis_entries[1]["ipTM"] == "0.31"
  assert lis_entries[1]["pLDDT_i"] == "86.8"
  assert lis_entries[1]["pLDDT_j"] == "81.2"
  assert lis_entries[1]["pLDDT"] == "83.3"
  assert lis_entries[1]["pTM"] == "0.55"
  assert lis_entries[1]["LIR_i"] == "41"
  assert lis_entries[1]["LIR_j"] == "32"
  assert lis_entries[1]["cLIR_i"] == "13"
  assert lis_entries[1]["cLIR_j"] == "12"
  assert lis_entries[1]["LIpLDDT_i"] == "73.4"
  assert lis_entries[1]["LIpLDDT_j"] == "73.7"
  assert lis_entries[1]["LIpLDDT"] == "73.5"
  assert lis_entries[1]["cLIpLDDT_i"] == "79.1"
  assert lis_entries[1]["cLIpLDDT_j"] == "79.3"
  assert lis_entries[1]["cLIpLDDT"] == "79.2"
  assert lis_entries[1]["len_i"] == "770"
  assert lis_entries[1]["len_j"] == "1269"
  assert lis_entries[1]["LIR_indices_i"] == "[59-98,694]"
  assert lis_entries[1]["LIR_indices_j"] == "[1205-1236]"
  assert lis_entries[1][
           "cLIR_indices_i"] == "[66,69,72-73,76-77,79-80,83-84,86-87,90]"
  assert lis_entries[1][
           "cLIR_indices_j"] == "[1211,1214-1215,1217-1218,1221-1222,1224-1225,1228-1229,1232]"
  assert lis_entries[1][
           "structure_file"] == "SPIKE_JN1__ECE1_HUMAN__CBD_seed-1945201344_sample-3_model.cif"
  assert lis_entries[2]["name"] == "HA_H5N1__BMP2_HUMAN__DMSO"
  assert lis_entries[2]["rank"] == "1945201344_2"
  assert lis_entries[2]["model"] == ""
  assert lis_entries[2]["chain_i"] == "BMP"
  assert lis_entries[2]["chain_j"] == "DMSO"
  assert lis_entries[2]["iLIS"] == "0.5254"
  assert lis_entries[3]["name"] == "HA_H5N1__BMP2_HUMAN__DMSO"
  assert lis_entries[3]["rank"] == "1945201344_0"
  assert lis_entries[3]["model"] == ""
  assert lis_entries[3]["chain_i"] == "BMP"
  assert lis_entries[3]["chain_j"] == "HA"
  assert lis_entries[3]["iLIS"] == "0.5189"
  assert lis_entries[4]["name"] == "HA_H5N1__BMP2_HUMAN__DMSO"
  assert lis_entries[4]["rank"] == "310698199_3"
  assert lis_entries[4]["model"] == ""
  assert lis_entries[4]["chain_i"] == "DMSO"
  assert lis_entries[4]["chain_j"] == "BMP"
  assert lis_entries[4]["iLIS"] == "0.5072"
