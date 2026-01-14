#!/bin/bash

script_path=$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")

export PATH="$script_path":$PATH
source "${script_path}/pairs-env/bin/activate"
