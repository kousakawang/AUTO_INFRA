### currently status

currently, AUTO_INFRA is a auto test project which can :
* read user's raw request, either from the raw launch server and benchmark commands like /sgl-workspace/AUTO_INFRA/raw_folder/raw_test_case.sh  or from the raw requirement document (files under /sgl-workspace/AUTO_INFRA/request_case)

* generate config files like /sgl-workspace/AUTO_INFRA/test_cases/config_20260409_124335.py

* execute python run_benchmark.py --config test_cases/config_20260409_124335.py to a. launch server  b. do benchmark c.  do result visualization and generate report(report example: /sgl-workspace/AUTO_INFRA/reports/benchmark_report_20260409_132912.md)



### reconstruct target:

1. breakdown the whole pipline in some stages, each stages can be executed as a skill-calling
2. the skill should be a standard claude code skill, which can be called by agent itself
3. so, when I let the agent do some task, it can decide how to finish the task with skill calling without a pre-defined worlflow
4. the most imortant target is, we can use the reconstructed project and agent to finish a more flexible task. Not only the fixed input/output concurrency .etc. But some tasks like:
*  user gives agent a SLO (which defines the max TTFT and TPOT), the agent can increase the max-concurrency to find the max throughput under the SLO.
* user gives agent some additional options, the agent can try to find the best option (for larger throughput) under certain scenario
* some more flexible task

### requirement:
you can do this in two stages
* stage1 : breakdown the pipline, do implement of the skills, call the whole example pipline with a new script
* stage2 : write a guideline for agent, tell it how to use these agents with the example of stage1. Then the next time, the agent can decide how to do without a predefined skill-calling script