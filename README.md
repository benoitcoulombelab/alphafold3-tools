# [AlphaFold 3](https://github.com/google-deepmind/alphafold3) Tools

Tools to run [AlphaFold 3](https://github.com/google-deepmind/alphafold3) using [Nextflow](https://www.nextflow.io) on [Alliance Canada](https://www.alliancecan.ca) servers.

To install the tools on Alliance Canada servers, see [INSTALL.md](INSTALL.md)

### Steps

1. [Prepare working environment](#Prepare-working-environment)
   1. [Set additional variables](#Set-additional-variables)
   2. [Download AlphaFold 3 database](#Download-AlphaFold-3-database)
2. [Running AlphaFold 3](#Running-AlphaFold-3)
   1. [Prepare JSON files](#Prepare-JSON-files)
   2. [Data step](#Data-step)
   3. [Inference step](#Inference-step)
3. [Scoring protein-protein interactions](#Scoring-protein-protein-interactions)

## Prepare working environment

Source the AlphaFold 3 tools init script.

```shell
source /project/def-coulomb/scripts/alphafold3-tools/alphafold3-init.sh
```

### Set additional variables

> [!IMPORTANT]
> Change `$SCRATCH/alphafold/dbs` by the actual AlphaFold's database folder.

```shell
database=$SCRATCH/alphafold/dbs
```

> [!IMPORTANT]
> Change `def-coulomb` by the actual account on which to run Nextflow.

```shell
account=def-coulomb
```

### Download AlphaFold 3 database

You can skip this step if you downloaded the database less than 2 months ago.

```shell
mkdir -p $database
bash fetch_databases.sh $database
```

## Running AlphaFold 3

### Prepare JSON files

```shell
mkdir json
fasta-pairs --baits baits.fasta --targets targets.fasta --output json -u -i
```

### Data step

```shell
sbatch nextflow-data.sh \
    --json 'json/*.json' \
    --database $database \
    --account $account
```

When running multiple proteins pairs, chances are high that some jobs will fail.
Before relaunching the data step, remove any JSON file that completed normally.

```shell
bash alphafold3-clear-complete-data.sh
```

Then relaunch the data step using the same command, see [Data step](#Data-step)

### Inference step

```shell
sbatch nextflow-inference.sh \
    --json 'data/**/*.json' \
    --database $database \
    --account $account
```

## Scoring protein-protein interactions

For ipTM, pTM and ranking scores, see [Confidence Metrics for AlphaFold 3](https://github.com/google-deepmind/alphafold3/blob/main/docs/output.md#confidence-metrics)

For LIS and Best LIS scores, see [AFM-LIS](https://github.com/flyark/AFM-LIS)

```shell
af3-scores \
    -i structures \
    -o interaction-scores.txt \
    -m iptm,lis
```
