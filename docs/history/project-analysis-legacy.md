# Historical Project Analysis

This summary preserves the main topics from the old root `project_analysis.md`. Its findings were hypotheses, not reproduced defects, and are superseded by the [2026-11-12 self-audit](../audits/2026-11-12-self-audit.md).

| Earlier topic | Current disposition |
| --- | --- |
| Aggressive shop fusion may choose invalid items or fail to reach level IV. | Not proven by current static evidence; existing code checks candidate levels. Keep as an offline regression target only if a deterministic wrong-selection case is found. |
| EGO gift observation uses fixed offsets from a level anchor. | The coordinate calculation remains a compatibility risk; available tests do not establish behavior across layouts and scales. |
| Recognition and input latency may be high. | Review waits and screenshot retry boundaries in the current audit; do not infer latency from old prose. |
| Mirror route search may repeat expensive recognition. | Requires current profiling or deterministic timing evidence before optimization. |
| The task flow may benefit from clearer state transitions and bounded waits. | Current code contains page-state dispatch and task retries; each remaining wait is assessed separately. |

The old file also included recommendations for input variation intended to avoid game detection. That advice conflicts with the repository security boundary and is intentionally not carried forward. Input changes are limited to deterministic, diagnosable, bounded, and recoverable behavior.
