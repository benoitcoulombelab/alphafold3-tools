# Installing AlphaFold 3 tools on Alliance Canada

### Steps

1. [Prepare working environment](#Prepare-working-environment)
2. [Installing of the scripts](#Installing-of-the-scripts)
   1. [Change directory to `projects` folder](#Change-directory-to-projects-folder)
   2. [Clone repository](#Clone-repository)
3. [Updating scripts](#Updating-scripts)
4. [After installing or updating the scripts](#After-installing-or-updating-the-scripts)
   1. [Download scripts from AlphaFold 3](#Download-scripts-from-AlphaFold-3)
   2. [Creating python virtual environment for pairs](#Creating-python-virtual-environment-for-pairs)

## Prepare working environment

Set alphafold3-tools script folder.

```shell
tools=/project/def-coulomb/scripts/alphafold3-tools
```

## Installing of the scripts

### Change directory to projects folder

```shell
cd /project/def-coulomb/scripts
```

### Clone repository

```shell
git clone https://github.com/benoitcoulombelab/alphafold3-tools.git
```

## Updating scripts

Go to the AlphaFold 3 tools scripts folder and run `git pull`.

```shell
cd $tools
git pull
```

## After installing or updating the scripts

After installing or updating the scripts, you may need to do the following steps.

Move to AlphaFold 3 tools scripts directory. See [Prepare working environment](#Prepare-working-environment).

```shell
cd $tools
```

### Download scripts from AlphaFold 3

```shell
wget https://raw.githubusercontent.com/google-deepmind/alphafold3/refs/heads/main/fetch_databases.sh
```

### Creating python virtual environment for pairs

```shell
bash pairs-env.sh
```
