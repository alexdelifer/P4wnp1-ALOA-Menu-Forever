#!/bin/bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

. "${SCRIPT_DIR}/library/shared.sh"

cd "${INSTALLDIR}" || exit 2
git stash || exit 3
git pull || exit 4
git stash pop || exit 5