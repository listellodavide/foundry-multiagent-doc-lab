#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -P "$(dirname "$0")" && pwd)
cd "$SCRIPT_DIR"

for environment in langgraph semantic-kernel autogen durable; do
    python=".venvs/$environment/bin/python"
    if [ ! -x "$python" ]; then
        echo "[FAIL] Missing .venvs/$environment. Run ./setup-extension-envs.sh first." >&2
        exit 1
    fi
    echo "[CHECK] Importing $environment extension environment..."
    "$python" -m pip check
done

.venvs/langgraph/bin/python -c 'from langgraph.graph import StateGraph; from langgraph.checkpoint.memory import InMemorySaver'
.venvs/semantic-kernel/bin/python -c 'from semantic_kernel.agents.runtime import InProcessRuntime'
.venvs/autogen/bin/python -c 'from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination; from autogen_ext.models.openai import AzureOpenAIChatCompletionClient'
.venvs/durable/bin/python -c 'import azure.functions; import azure.durable_functions'

".venv/bin/python" -m pytest -q -m "not live"
echo "[PASS] Extension contracts and dependencies passed."
