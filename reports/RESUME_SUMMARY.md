# Resume Summary

## Project Title

Agentic RL Rollout and Validation Profiling for WebShop Agents

Alternative shorter title:

AgentRolloutProfiler: Bottleneck Analysis for Agentic RL Evaluation

## One-Line Version

Built a profiling pipeline for verl-agent + WebShop Agentic RL, ruled out
environment stepping as the main bottleneck, quantified validation scaling, and
proposed an eval-scheduling strategy estimated to reduce exploratory training
wall-clock by 23.6%.

## Resume Bullets

- Built a profiling-first systems project for WebShop Agentic RL on verl-agent,
  instrumenting environment manager/worker steps and parsing trainer logs to
  break down generation, validation, reward, reference log-prob, and actor
  update costs.
- Measured WebShop environment interaction at only 35-47 ms per step, while
  validation steps took 350-450s in RL logs, ruling out environment stepping,
  search caching, and parser optimization as primary bottlenecks for the
  observed workload.
- Quantified validation scaling across eval8/eval16/eval64 runs
  (244s/360s/554s wall-clock) and showed eval64 environment stepping accounted
  for only about 11.5s, shifting optimization focus from WebShop internals to
  validation/runtime scheduling.
- Designed an evaluation-scheduling strategy using small frequent evals plus
  final full eval, estimating 23.6% wall-clock reduction for a 32-step
  exploratory RL run without changing reward, policy update, or benchmark
  semantics.
- Verified checkpoint-saving feasibility and limitations: verl-agent actor
  checkpoints can be saved but were about 219G and not directly
  HuggingFace-loadable, defining a clear boundary for final model-quality
  comparison claims.

## Interview Narrative

The project started from the assumption that WebShop environment interaction
might be the bottleneck in Agentic RL. I added lightweight instrumentation to
the environment manager and WebShop worker, then combined those live events with
verl-agent trainer log parsing.

The first important result was negative but useful: WebShop steps were only
tens of milliseconds, while validation-heavy trainer steps were hundreds of
seconds. Search repetition was also near zero in the measured runs, so cache and
parser optimization would not solve the real bottleneck.

I then measured eval8/eval16/eval64 scaling and found that eval64 took about
554s wall-clock, while all measured environment steps accounted for only about
11.5s. This shifted the project from environment optimization to validation
scheduling.

The final systems recommendation was to use smaller validation sets for frequent
progress checks and reserve full eval64 for final reporting. Based on measured
timings, this would reduce a 32-step exploratory run by about 23.6% wall-clock.
I also checked whether final policy quality comparison was feasible: checkpoint
saving works, but saved actor checkpoints are very large and cannot be directly
loaded as HuggingFace models, so final quality-equivalence claims require a
separate export or val-only resume path.

## What Not To Claim

Do not claim:

- WebShop itself was optimized.
- The model quality improved.
- The schedule is proven quality-equivalent to full eval64.
- `global_step_*/actor` can be directly evaluated as a HuggingFace model.

Safe claim:

- The project performed profiling-driven bottleneck analysis and identified a
  low-risk evaluation scheduling optimization for exploratory Agentic RL runs.
