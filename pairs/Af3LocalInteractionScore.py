"""
Code of this file was copied from https://github.com/flyark/AFM-LIS.
"""

import json
from collections import Counter

import numpy as np
import pandas as pd
from scipy.spatial.distance import pdist, squareform


def transform_pae_matrix(pae_matrix, pae_cutoff):
  # Initialize the transformed matrix with zeros
  transformed_pae = np.zeros_like(pae_matrix)

  # Apply transformation: pae = 0 -> score = 1, pae = cutoff -> score = 0, above cutoff -> score = 0
  # Linearly scale values between 0 and cutoff to fall between 1 and 0
  within_cutoff = pae_matrix < pae_cutoff
  transformed_pae[within_cutoff] = 1 - (pae_matrix[within_cutoff] / pae_cutoff)

  return transformed_pae


def calculate_mean_lis(transformed_pae, subunit_number):
  # Calculate the cumulative sum of protein lengths to get the end indices of the submatrices
  cum_lengths = np.cumsum(subunit_number)

  # Add a zero at the beginning of the cumulative lengths to get the start indices
  start_indices = np.concatenate(([0], cum_lengths[:-1]))

  # Initialize an empty matrix to store the mean LIS
  mean_lis_matrix = np.zeros((len(subunit_number), len(subunit_number)))

  # Iterate over the start and end indices
  for i in range(len(subunit_number)):
    for j in range(len(subunit_number)):
      # Get the start and end indices of the interaction submatrix
      start_i, end_i = start_indices[i], cum_lengths[i]
      start_j, end_j = start_indices[j], cum_lengths[j]

      # Get the interaction submatrix
      submatrix = transformed_pae[start_i:end_i, start_j:end_j]

      # Calculate the mean LIS, considering only non-zero values
      mean_lis = submatrix[submatrix > 0].mean()

      # Store the mean LIS in the matrix
      mean_lis_matrix[i, j] = mean_lis

  return mean_lis_matrix


def calculate_contact_map(cif_file, distance_threshold: float = 8):
  def read_cif_lines(cif_path):
    with open(cif_path, 'r') as file:
      lines = file.readlines()

    residue_lines = []
    for line in lines:
      if line.startswith('ATOM') and (
          'CB' in line or 'GLY' in line and 'CA' in line):
        residue_lines.append(
            line.strip())  # Store the line if it meets the criteria for ATOM

      if line.startswith('ATOM') and 'P   ' in line:
        residue_lines.append(
            line.strip())  # Store the line if it meets the criteria for ATOM

      elif line.startswith('HETATM'):
        residue_lines.append(line.strip())  # Store all HETATM lines

    return residue_lines

  def lines_to_dataframe(residue_lines):
    # Split lines and create a list of dictionaries for each atom
    data = []
    for line in residue_lines:
      parts = line.split()
      # Correctly convert numerical values
      for i in range(len(parts)):
        try:
          parts[i] = float(parts[i])
        except ValueError:
          pass
      data.append(parts)

    df = pd.DataFrame(data)

    # Add line number column
    df.insert(0, 'residue', range(1, 1 + len(df)))

    return df

  # Read lines from CIF file
  residue_lines = read_cif_lines(cif_file)

  # Convert lines to DataFrame
  df = lines_to_dataframe(residue_lines)

  # Assuming the columns for x, y, z coordinates are at indices 11, 12, 13 after insertion
  coordinates = df.iloc[:, 11:14].to_numpy()

  distances = squareform(pdist(coordinates))

  # Assuming the column for atom names is at index 3 after insertion
  has_phosphorus = df.iloc[:, 3].apply(lambda x: 'P' in str(x)).to_numpy()

  # Adjust the threshold for phosphorus-containing residues
  adjusted_distances = np.where(
      has_phosphorus[:, np.newaxis] | has_phosphorus[np.newaxis, :],
      distances - 4, distances)

  contact_map = np.where(adjusted_distances < distance_threshold, 1, 0)
  return contact_map


def local_interaction_score(af3_json: str, af3_structure: str,
    pae_cutoff: float = 12, distance_cutoff: float = 8,
    subunit_one: int = 0, subunit_two: int = 1):
  """
  Returns local interaction score between first subunit and second subunit as defined in this paper:
  https://www.biorxiv.org/content/10.1101/2024.02.19.580970v1

  Returned value is a tuple of iLIS, LIS and LIA score.

  :param af3_json: path to either '*_full_data_?.json' or '*_confidences.json' file.
  :param af3_structure: path to '*.cif' file that matches the af3_json file.
  :param pae_cutoff: cutoff for PAE values
  :param distance_cutoff: cutoff for distance between residues when computing local interaction score
  :param subunit_one: identifier of first subunit
  :param subunit_two: identifier of second subunit
  :return: local interaction score between first subunit and second subunit
  """
  json_data = json.load(open(af3_json, 'rb'))

  token_chain_ids = json_data['token_chain_ids']
  chain_residue_counts = Counter(token_chain_ids)
  subunit_number = list(chain_residue_counts.values())
  pae_matrix = np.array(json_data['pae'], dtype=float)
  pae_matrix = np.nan_to_num(pae_matrix)

  # ----------------------------------------------
  # 2) Transform PAE matrix => LIS
  # ----------------------------------------------
  transformed_pae_matrix = transform_pae_matrix(pae_matrix, pae_cutoff)
  transformed_pae_matrix = np.nan_to_num(transformed_pae_matrix)

  # A binary map (1 where LIS>0, else 0)
  lia_map = np.where(transformed_pae_matrix > 0, 1, 0)

  mean_lis_matrix = calculate_mean_lis(transformed_pae_matrix, subunit_number)
  mean_lis_matrix = np.nan_to_num(mean_lis_matrix)

  # ----------------------------------------------
  # 3) Contact map => cLIA
  # ----------------------------------------------
  contact_map = calculate_contact_map(af3_structure, distance_cutoff)

  combined_map = np.where(
      (transformed_pae_matrix > 0) & (contact_map == 1),
      transformed_pae_matrix,
      0
  )
  mean_clis_matrix = calculate_mean_lis(combined_map, subunit_number)
  mean_clis_matrix = np.nan_to_num(mean_clis_matrix)

  # ----------------------------------------------
  # 4) Count-based metrics: LIA, LIR, cLIA, cLIR
  #    plus local (per-subunit) residue indices
  # ----------------------------------------------
  subunit_count = len(subunit_number)
  lia_matrix = np.zeros((subunit_count, subunit_count), dtype=int)

  # For extracting submatrices
  cum_lengths = np.cumsum(subunit_number)
  starts = np.concatenate(([0], cum_lengths[:-1]))

  # subunit one spans [start_one, end_one), subunit two spans [start_two, end_two)
  start_one, end_one = starts[subunit_one], cum_lengths[subunit_one]
  start_two, end_two = starts[subunit_two], cum_lengths[subunit_two]

  # Submatrix for LIS-based local interactions (binary)
  interaction_submatrix = lia_map[start_one:end_one, start_two:end_two]
  lia_matrix[subunit_one, subunit_two] = np.count_nonzero(
      interaction_submatrix)

  i_lis = np.sqrt(
      mean_lis_matrix[subunit_one, subunit_two] * mean_clis_matrix[
        subunit_one, subunit_two])

  return (i_lis, mean_lis_matrix[subunit_one, subunit_two],
          lia_matrix[subunit_one, subunit_two])
