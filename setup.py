from setuptools import setup, find_packages

setup(
    name="af3-tools",
    version="0.4",
    packages=find_packages(),
    author="Christian Poitras",
    author_email="christian.poitras@ircm.qc.ca",
    description="Find interactions using AlphaFold",
    keywords="bioinformatics, AlphaFold",
    url="https://github.com/benoitcoulombelab/alphafold3-tools.git",
    license="GNU General Public License version 3",
    classifiers=[
      "License :: OSI Approved :: GNU General Public License version 3"
    ],
    install_requires=[
      "biopython>=1.84",
      "numpy>=2.3.3",
      "pandas>=2.3.3",
      "scipy>=1.16.2",
      "tqdm>=4.67.1"
    ],
    entry_points={
      "console_scripts": [
        "af3-score = af3tools.Af3Score:main",
        "delete-fasta = af3tools.DeleteFasta:main",
        "fasta-id = af3tools.FastaId:main",
        "fasta-to-json-sequence = af3tools.FastaToJsonSequence:main",
        "id-convert = af3tools.IdConvert:main",
        "json-pairs = af3tools.JsonPairs:main",
        "list-files = af3tools.ListFiles:main",
        "pair-sizes = af3tools.PairSizes:main",
        "split-fasta = af3tools.SplitFasta:main",
      ]
    }
)
