#!/usr/bin/env bash
#https://github.com/volcengine/verl
set -euo pipefail
set -x
export PROJ_ROOT=/absolute/path/to/your/project

python3 -m verl.trainer.main_ppo \
    custom_reward_function.path=PROJ_ROOT/reward_function.py \
    reward_model.reward_manager=batch \
    reward_model.launch_reward_fn_async=True \
    algorithm.adv_estimator=grpo \
    algorithm.use_kl_in_reward=False \
    data.train_files=PROJ_ROOT/rl_train.parquet \
    data.val_files=PROJ_ROOT/rl_val.parquet \
    data.train_batch_size=96 \
    data.max_prompt_length=4096 \
    data.max_response_length=1024 \
    data.filter_overlong_prompts=True \
    data.truncation=error \
    actor_rollout_ref.model.path=PROJ_ROOT/your_model \
    actor_rollout_ref.model.use_remove_padding=True \
    actor_rollout_ref.model.enable_gradient_checkpointing=True \
    actor_rollout_ref.actor.optim.lr=1e-6 \
    actor_rollout_ref.actor.ppo_mini_batch_size=24 \
    actor_rollout_ref.actor.ppo_micro_batch_size_per_gpu=4 \
    actor_rollout_ref.actor.use_kl_loss=True \
    actor_rollout_ref.actor.kl_loss_coef=0.001 \
    actor_rollout_ref.actor.kl_loss_type=low_var_kl \
    actor_rollout_ref.actor.entropy_coeff=0 \
    actor_rollout_ref.actor.fsdp_config.param_offload=False \
    actor_rollout_ref.actor.fsdp_config.optimizer_offload=False \
    actor_rollout_ref.ref.fsdp_config.param_offload=True \
    actor_rollout_ref.rollout.name=vllm \
    actor_rollout_ref.rollout.n=5 \
    actor_rollout_ref.rollout.tensor_model_parallel_size=1 \
    actor_rollout_ref.rollout.gpu_memory_utilization=0.6 \
    actor_rollout_ref.rollout.log_prob_micro_batch_size_per_gpu=4 \
    actor_rollout_ref.ref.log_prob_micro_batch_size_per_gpu=4 \
    trainer.critic_warmup=0 \
    trainer.logger="[console,wandb]" \
    trainer.project_name=rebuttal-agent \
    trainer.experiment_name=RebuttalAgent \
    trainer.n_gpus_per_node=3 \
    trainer.nnodes=1 \
    trainer.val_before_train=True \
    trainer.save_freq=25 \
    trainer.test_freq=25 \
    trainer.total_epochs=2 \
    trainer.default_local_dir=PROJ_ROOT/your_output_path \
    "$@"