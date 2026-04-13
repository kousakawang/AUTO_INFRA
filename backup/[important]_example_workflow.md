
1.basic files/folder:
* launch_server_template : include basic launch server command template
* benchmark_template: include basic benchmark command template
* OPT: include optimization when launch server. ENV_OPT: is the env_var list which contains some opt env_vars SERVER_ARG_OPT is server arg list


2. user input:

* a user will input information like the following python dictionary (you can decide the format of input file, either python/yaml/josn etc. is ok)


```python
user_config = {
    
  "model_paths" : ["/data01/models/Qwen3.5-9B", "/data01/models/Qwen3-VL-8B"],
  "model_test_times" : [3,1],# this means first model（9B） we will launch 3 server to test, the second model(8B) we will launch 1 server to test 
  "model_deploy_method":["tp1", "tp2", "tp1", "tp1"], # a list , which's length must equal to  sum(basic_input["model_test_times"]), this case means 9B's three server use (tp1/tp2/tp1) while 8B's server use tp1
  "device_id":[[0], [1,2], [3], [4]], # same as model_deploy_method, when you launch server set CUDA_VISIBLE_DEVICES as device_id here, note each member in this list is also a list for we may use more than one device to deploy the model
  "basic_template_id" : [0,0,0,1], # this means the first 3 server use template 0 and the last server use template
  "port":[8080, 8070, 8060, 8050],
  "env_opt_id" : [[-1],[0], [-1], [-1]], # which env_opt will be used for launch server. if -1 use no opt
  "server_args_opt_id":[[0],[0],[1],[1]], # which server opt args will be used for launch server, if -1 use no opt.
  "additional_option":[["--context-length 262144 --reasoning-parser qwen3"],["--context-length 262144 --reasoning-parser qwen3"],["--context-length 262144 --reasoning-parser qwen3"],[None]], # additonal message
  #following will be the benchmark config
  "benchmark_case_num":[[3],[3], [3], [1]] # first 3 service will do 3 benchmark cases, while the last one only do 1 benchmark case
  "benchmark_inputlen":[[32,32,32], [32,32,32], [32,64,32], [32]], # [32,32,32] means for service1, we will do 3 benchmark, each's input will be 32. [NOTE] : all bench config follow if the length of config is less than the server's benchmark_case_num, it will expand to the benchmark_case_num with the latest config value, for example, if the firstly [32,32,32] of benchmark_inputlen is [32], it will expand to [32,32,32] automatically
  "benchmark_outputlen":[[64,64,64], [64,64,64],[64,32,32], [64]] # same with input
  "benchmark_image_size" :[["448x448", "448x448", "448x448"], ["448x448", "448x448", "448x448"], ["448x448", "448x448", "448x448"], ["1080x720"]], # per benchmark's image size
  "benchmark_image_count":[[1,1,1],[1,1,1],[1,1,1],[1]],
  "benchmark_max_concurrency":[[10,20,30], [10,20,30],[10,20,30], [10]],
}

# common benchmark config, all the config have default value and usually, user do not need to modify this
pipline_config = {
  "per_config_benchmark_times": 5, #  for each benchmark config test 5 times
  "prompt_num_dvide_max_concurrency": 6, # prompt_num use to benchmark = 6 * max_concurrency
  "data_watch_policy":"remove_min_max", # when we compute average throughput remove min/max data
  "max_existed_service_num":2, # we can  at most let 2 services keep alive simultanously
  "do_visuallize":  True, # if False skip visualizing and report generation
  "SLO":[1e8, 1e8], # a two member list which contains[TTFT_MAX, TPOT_MAX], report should only include throught data in which case the  TTFT <= TTFT_MAX and TPOT <= TPOT_MAX
}

```


3. generate full launch service commands and its benchmark commands
* now we can generate 4 launch server commands on 4 ports
* we also have 4 benchmark command sets(each set inlcude  serval benmark command)


4. launch server and do benchmark 
* according to pipline_config, we will launch service 1 and sevice 2, do benchmark for them  with their own benchmark commands set
* if service 1 or service 2 finished all benchmark task, we need to kill it and luanch service 3
* the same for service 4

5. write summary and do visualize
* after all the benchmark task finished, we will do the visualize and summary task
* we need to generate tables and images, and we will fill all benchmark_datas in a table only if when :
  * they are the same model's benchmark data
  * they hold the same benchmark config (include input_len/output_len/image_size/image_count/max_concurrency)
  * they use the same launch server template_id and benchmark template_id
  * they use the same model_deploy_method
  * in a summary : the above part should be fixed for all data in the table,while server_args_opt_id/server_args_opt_id can change

* for each table, we generate a figure, the x-axis is the server_args_opt_id/server_args_opt_id info and the y_axis is the throughput, the figure's title is the fixed part info's combiniation

6. other infomation 
* a full version lunch_server command example is in launch_server_basic.sh
* a full version benchmark command example is in benchmark_cmd_basic.sh
* the benchmark command's result example is in benmark_result_example.md