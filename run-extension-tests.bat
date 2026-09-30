@echo off
setlocal EnableExtensions
cd /d "%~dp0" || exit /b 1

for %%E in (langgraph semantic-kernel autogen durable) do (
    if not exist ".venvs\%%E\Scripts\python.exe" (
        echo [FAIL] Missing .venvs\%%E. Run setup-extension-envs.bat first.
        exit /b 1
    )
    echo [CHECK] Importing %%E extension environment...
    ".venvs\%%E\Scripts\python.exe" -m pip check || exit /b 1
)

".venvs\langgraph\Scripts\python.exe" -c "from langgraph.graph import StateGraph; from langgraph.checkpoint.memory import InMemorySaver" || exit /b 1
".venvs\semantic-kernel\Scripts\python.exe" -c "from semantic_kernel.agents.runtime import InProcessRuntime" || exit /b 1
".venvs\autogen\Scripts\python.exe" -c "from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination; from autogen_ext.models.openai import AzureOpenAIChatCompletionClient" || exit /b 1
".venvs\durable\Scripts\python.exe" -c "import azure.functions; import azure.durable_functions" || exit /b 1

".venv\Scripts\python.exe" -m pytest -q -m "not live"
echo [PASS] Extension contracts and dependencies passed.
