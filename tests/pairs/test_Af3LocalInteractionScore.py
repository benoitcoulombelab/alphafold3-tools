import shutil
import io
import os
import statistics
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pairs import Af3LocalInteractionScore


@pytest.fixture
def mock_testclass():
  _local_interaction_score = Af3LocalInteractionScore.local_interaction_score
  yield
  Af3LocalInteractionScore.local_interaction_score = _local_interaction_score


def test_local_interaction_score(testdir, mock_testclass):
  confidences = Path(__file__).parent.joinpath(
      "ha_h5n1__bmp2_human_confidences.json")
  model = Path(__file__).parent.joinpath("ha_h5n1__bmp2_human_model.cif")
  scores = Af3LocalInteractionScore.local_interaction_score(str(confidences), str(model))
  assert scores[0] == pytest.approx(0.364201909)
  assert scores[1] == pytest.approx(0.226591249)
  assert scores[2] == pytest.approx(26541)
