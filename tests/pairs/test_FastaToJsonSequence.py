import json
import os.path
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from pairs import FastaToJsonSequence, FastaId


@pytest.fixture
def mock_testclass():
  _fasta_to_json_sequence = FastaToJsonSequence.fasta_to_json_sequence
  _sequence_to_json = FastaToJsonSequence.sequence_to_json
  _parse_fasta = FastaToJsonSequence.parse_fasta
  _fasta_id = FastaId.fasta_id
  yield
  FastaToJsonSequence.fasta_to_json_sequence = _fasta_to_json_sequence
  FastaToJsonSequence.sequence_to_json = _sequence_to_json
  FastaToJsonSequence.parse_fasta = _parse_fasta
  FastaId.fasta_id = _fasta_id


def test_main(testdir, mock_testclass):
  FastaToJsonSequence.fasta_to_json_sequence = MagicMock()
  FastaToJsonSequence.main([])
  FastaToJsonSequence.fasta_to_json_sequence.assert_called_once_with(
      fasta_files=["-"], output_dir="")


def test_main_parameters(testdir, mock_testclass):
  fasta1 = "abc.fasta"
  open(fasta1, 'w').close()
  fasta2 = "def.fasta"
  open(fasta2, 'w').close()
  output_dir = "output"
  os.mkdir(output_dir)
  FastaToJsonSequence.fasta_to_json_sequence = MagicMock()
  FastaToJsonSequence.main(["-f", fasta1, fasta2, "-o", output_dir])
  FastaToJsonSequence.fasta_to_json_sequence.assert_called_once_with(
      fasta_files=[fasta1, fasta2], output_dir=output_dir)


def test_main_long_parameters(testdir, mock_testclass):
  fasta1 = "abc.fasta"
  open(fasta1, 'w').close()
  fasta2 = "def.fasta"
  open(fasta2, 'w').close()
  output_dir = "output"
  os.mkdir(output_dir)
  FastaToJsonSequence.fasta_to_json_sequence = MagicMock()
  FastaToJsonSequence.main(["--fasta", fasta1, fasta2, "--output", output_dir])
  FastaToJsonSequence.fasta_to_json_sequence.assert_called_once_with(
      fasta_files=[fasta1, fasta2], output_dir=output_dir)


def test_fasta_to_json_sequence(testdir, mock_testclass):
  fasta1 = str(Path(__file__).parent.joinpath("P19388__P36954.fasta"))
  fasta2 = str(Path(__file__).parent.joinpath("P62487.fasta"))
  output_dir = "output"
  os.mkdir(output_dir)
  FastaToJsonSequence.fasta_to_json_sequence(fasta_files=[fasta1, fasta2], output_dir=output_dir)
  assert os.path.isfile(f"{output_dir}/RPAB1_HUMAN.json")
  with open(f"{output_dir}/RPAB1_HUMAN.json", 'r') as json_in:
    json_data = json.load(json_in)
    assert "protein" in json_data
    assert "id" in json_data["protein"]
    assert json_data["protein"]["id"] == "RPAB"
    assert "sequence" in json_data["protein"]
    assert json_data["protein"]["sequence"] == "MDDEEETYRLWKIRKTIMQLCHDRGYLVTQDELDQTLEEFKAQSGDKPSEGRPRRTDLTV" \
                                               "LVAHNDDPTDQMFVFFPEEPKVGIKTIKVYCQRMQEENITRALIVVQQGMTPSAKQSLVD" \
                                               "MAPKYILEQFLQQELLINITEHELVPEHVVMTKEEVTELLARYKLRENQLPRIQAGDPVA" \
                                               "RYFGIKRGQVVKIIRPSETAGRYITYRLVQ"
    assert "description" in json_data["protein"]
    assert json_data["protein"]["description"] == "RPAB1_HUMAN"
  assert os.path.isfile(f"{output_dir}/RPB9_HUMAN.json")
  with open(f"{output_dir}/RPB9_HUMAN.json", 'r') as json_in:
    json_data = json.load(json_in)
    assert "protein" in json_data
    assert "id" in json_data["protein"]
    assert json_data["protein"]["id"] == "RPB"
    assert "sequence" in json_data["protein"]
    assert json_data["protein"]["sequence"] == "MEPDGTYEPGFVGIRFCQECNNMLYPKEDKENRILLYACRNCDYQQEADNSCIYVNKITH" \
                                               "EVDELTQIIADVSQDPTLPRTEDHPCQKCGHKEAVFFQSHSARAEDAMRLYYVCTAPHCG" \
                                               "HRWTE"
    assert "description" in json_data["protein"]
    assert json_data["protein"]["description"] == "RPB9_HUMAN"
  assert os.path.isfile(f"{output_dir}/RPB7_HUMAN.json")
  with open(f"{output_dir}/RPB7_HUMAN.json", 'r') as json_in:
    json_data = json.load(json_in)
    assert "protein" in json_data
    assert "id" in json_data["protein"]
    assert json_data["protein"]["id"] == "RPB"
    assert "sequence" in json_data["protein"]
    assert json_data["protein"]["sequence"] == "MFYHISLEHEILLHPRYFGPNLLNTVKQKLFTEVEGTCTGKYGFVIAVTTIDNIGAGVIQ" \
                                               "PGRGFVLYPVKYKAIVFRPFKGEVVDAVVTQVNKVGLFTEIGPMSCFISRHSIPSEMEFD" \
                                               "PNSNPPCYKTMDEDIVIQQDDEIRLKIVGTRVDKNDIFAIGSLMDDYLGLVS"
    assert "description" in json_data["protein"]
    assert json_data["protein"]["description"] == "RPB7_HUMAN"
