from setuptools import setup, find_packages

setup(
    name="pairs",
    version="0.3",
    packages=find_packages(),
    author="Christian Poitras",
    author_email="christian.poitras@ircm.qc.ca",
    description="Find interactions using AlphaFold",
    keywords="bioinformatics, AlphaFold",
    url="https://github.com/benoitcoulombelab/pairs.git",
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
        "af3-score = pairs.Af3Score:main",
        "delete-fasta = pairs.DeleteFasta:main",
        "fasta-id = pairs.FastaId:main",
        "id-convert = pairs.IdConvert:main",
        "json-pairs = pairs.JsonPairs:main",
        "list-files = pairs.ListFiles:main",
        "pair-sizes = pairs.PairSizes:main",
        "split-fasta = pairs.SplitFasta:main",
      ]
    }
)
