# Research provenance

Date: 20 September 2026.

## Tools actually used in this phase

- Agent Reach skill: read its full instructions and search/web backend references; used it to route research CLI discovery.
- Exa through `mcporter call exa.web_search_exa`: searched `agent harness optimization regression constraints mutation budget cost Pareto Self-Harness GEPA`, six results. The sandbox request failed on network negotiation; the approved network-capable retry succeeded and surfaced HarnessBank and current GEPA documentation.
- Web research tools: opened supplied arXiv identifiers and HTML methods; searched for HarnessFix, Meta-Harness, AutoHarness and related budget/retention work; checked primary abstract pages for supporting research.
- Shell read-only checks: checked the new project path and kept the prior medical-paper project separate.
- `apply_patch`: first authored the specification package, then the bounded pilot after the user selected Kaggle and requested a runnable GitHub repository.
- `agent-reach check-update`: attempted; DNS lookup failed after the tool's retries. No update installed and no update availability claim made.

No social media evidence was needed for these technical claims. No paid API inference occurred locally. Jina Reader was available in the skill instructions but was not used in this phase. The subsequent private GitHub publication is explicitly user-authorized; it is not a public research release.

## Important research decisions

1. Verify references before repeating the proposed novelty claim.
2. Add HarnessFix and HarnessBank to the closest related work because both materially overlap with the proposed contribution.
3. Change the working claim from invention of regression-safe evolution to a controlled study of gate and edit-budget choices.
4. Treat this as a separate general tool-agent study, not as additional evidence for the completed medical-AI manuscript.
5. Keep implementation after the literature map and protocol, as requested.

## What remains unresolved

- Free Kaggle selected by the user; GPU availability/quota and actual execution still require the user's Kaggle session. No paid budget assumed.
- Final model and proposer revisions, licenses, quantization and runtime settings.
- Whether pilot evidence supports a feasible main experiment and adequate precision.
- Full-method/code audit for the more distant papers in the screening map.
- Any broader novelty or state-of-the-art comparison beyond the controlled mechanism study.

The source map links papers directly and distinguishes detailed method inspection from abstract-level screening. It should not be described as 15 complete paper reproductions or a comprehensive systematic review.

## Kaggle implementation phase

The Jupyter Notebooks skill was read and used to structure a tutorial notebook with setup, bounded execution, checks and output export. Kaggle's official notebook documentation and official Docker repository were checked; Qwen's model card and the pinned Transformers release page were opened. Current quota amounts are deliberately not promised.

Local verification uses standard-library unit tests, reference solutions for 90 synthetic instances, a mock end-to-end optimization/freeze/test/report cycle, Python compilation and notebook structure/code-cell validation.

The notebook was run in the user's private Kaggle workspace on 20 September 2026. The source dataset stayed private, Internet was enabled, and Kaggle allocated two Tesla T4 devices while the code used `cuda:0` only. All 26 repository tests passed in Kaggle before inference.

The first real run exposed non-finite float16 sampling scores and `!`-only generations. That run was excluded as runtime corruption, not counted as task failure. A float32 preflight produced sane JSON, after which a clean frozen run completed. The corrected artifact reports 3/5 final-task success for every arm, zero lost baseline successes, 602.6 mean tokens per task, and 918 search tokens for each learned arm. All three proposals were rejected for a forbidden nested schema, so this run demonstrates execution feasibility but no harness optimization gain. The complete artifact is `results/roho-smoke-results.zip`; its interpretation is in `results/README.md`.

The private GitHub workflow is manual-only (`workflow_dispatch`), so publishing does not automatically start Actions jobs or consume a private Actions allowance. The default computational work is performed on the user's free Kaggle allocation.
