#!/bin/bash

# Tool designed to just run as many checks as possible against inputs
# to stress test pagegraph-query.

CURRENT_DIR=$(dirname "$0");
PROJECT_ROOT="$CURRENT_DIR/../../../..";
TEST_GRAPHS_DIR="$PROJECT_ROOT/pagegraph/tests/assets/graphs";
VENV_ROOT="$PROJECT_ROOT/..";
SCRATCH_FILE=$(mktemp);
TEST_SUBCOMMANDS="validate subframes requests scripts";

source "$VENV_ROOT/bin/activate";

# If not called with a single argument of the path to a directory of graph
# files, then use the graph files used for tests.
if [[ "$#" -eq 0 ]]; then
  GRAPH_DIR=$TEST_GRAPHS_DIR;
elif [[ ! -d "$1" ]]; then
  echo "Provided argument must be the path to a directory." 1>&2;
  exit 1;
else
  GRAPH_DIR=$1;
fi;

if [[ -t "$SCRATCH_FILE" ]]; then
  rm "$SCRATCH_FILE";
fi;

for GRAPH in "$GRAPH_DIR"/*; do
  if ! echo "$GRAPH" | grep -qE '\.graphml$'; then
    continue;
  fi;

  for SUBCOMMAND in $TEST_SUBCOMMANDS; do
    if "$PROJECT_ROOT/run.py" "$SUBCOMMAND" "$GRAPH" > /dev/null; then
      echo "✅ - $SUBCOMMAND $GRAPH";
    else :
      echo "❌ - $SUBCOMMAND $GRAPH";
      exit 1;
    fi;
  done;
done;
