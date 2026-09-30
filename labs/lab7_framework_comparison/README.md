# Lab 7: The same multi-agent review in three frameworks

October 2026 workshop. **Time:** 195 minutes. Advanced extension-day lab.

> **Advanced Python required.** You should be comfortable with async runtimes, graph and team
> orchestration, isolated environments, typed contracts and lifecycle cleanup.

All variants read the same packet, produce the same `DecisionRecord`, and use the same deterministic
policy judge. This keeps the comparison focused on orchestration rather than prompt differences.

1. Create the isolated environments with `setup-extension-envs.bat` or
   `./setup-extension-envs.sh`.
2. Complete the LangGraph supervisor graph in `start/langgraph_review.py`.
3. Complete the Semantic Kernel concurrent orchestration in `start/semantic_kernel_review.py`.
4. Complete the AutoGen selector group chat in `start/autogen_review.py`.
5. Score `out/lab7_*.json` together and complete `framework-comparison.md` using measured evidence.

The shared contract is `async run_review() -> DecisionRecord`. Domain agents may extract facts;
`shared.policy.build_record` remains the final authority. Each implementation must bound agent
turns, preserve session state, expose a human escalation point, and close its model/runtime client.
