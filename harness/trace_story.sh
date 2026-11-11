#!/usr/bin/env bash
# Prints one agentic storyteller run turn by turn: the sentence the storyteller added,
# the critic's verdict and the stop_when decision.
#
# Usage: harness/trace_story.sh <storyteller execution id> [conductor CLI profile]
#
# The storyteller never replies with text; each turn it calls the critic with the whole
# story so far. The new sentence is that request minus the previous turn's request.
set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "Usage: $0 <storyteller execution id> [conductor CLI profile]" >&2
  exit 2
fi

PROFILE_ARGS=()
if [[ $# -eq 2 ]]; then
  PROFILE_ARGS=(--profile "$2")
fi

# ${arr[@]+...} keeps an empty array legal under set -u on macOS bash 3.2.
conductor ${PROFILE_ARGS[@]+"${PROFILE_ARGS[@]}"} workflow get-execution -c "$1" | jq -r '
  [.tasks[]] as $t
  | "\(.workflowName) \(.workflowId): \(.status)\n",
    (([$t[] | select(.taskType == "LLM_CHAT_COMPLETE")] | length) as $turns
    | range(1; $turns + 1) as $n
    | ($t[] | select(.referenceTaskName == "python_storyteller_llm__\($n)")) as $llm
    | ([$t[] | select(.referenceTaskName == "python_storyteller_llm__\($n - 1)")][0].outputData.toolCalls[0].inputParameters.request // "") as $prev
    | ($llm.outputData.toolCalls[0].inputParameters.request) as $story
    | ([$t[] | select(.referenceTaskName | test("^toolu_.*__\($n)$"))][0].outputData.result // {}) as $verdict
    | ([$t[] | select(.referenceTaskName == "python_storyteller_stop_when__\($n)")][0].outputData // {}) as $stop
    | "### Turn \($n)  (storyteller tokens \($llm.outputData.promptTokens) in / \($llm.outputData.completionTokens) out)",
      (if $story == null then
         "NO CRITIC CALL; storyteller replied: \($llm.outputData.result | tostring)"
       elif ($prev != "" and ($story | startswith($prev))) then
         "NEW SENTENCE: \($story[($prev | length):] | ltrimstr(" "))"
       else
         "STORY SENT TO CRITIC:\n\($story)"
       end),
      "CRITIC: done=\($verdict.done) missing=\($verdict.missing | tostring)",
      "  note: \($verdict.note)",
      "STOP_WHEN: \($stop | tostring)\n"),
    "FINAL STORY:\n\([$t[] | select(.taskType == "LLM_CHAT_COMPLETE") | .outputData.toolCalls[0].inputParameters.request // empty] | last)"'
