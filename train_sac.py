import gym
import numpy as np
import itertools
import torch
import logging
from pathlib import Path
from sac.sac import SAC
from sac.replay_memory import ReplayMemory
from perception.utils import load_model, process_observation
from perception.generate_AE_data import generate_action
from torch.utils.tensorboard import SummaryWriter
from datetime import datetime

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
"""Set the device globally if a GPU is available."""

# TODO T: Parameters here or in Algo itself?
def train(seed: int = 69,
          batch_size: int = 256,
          num_steps: int = 1000000,
          updates_per_step: int = 1,
          start_steps: int = 10000,
          replay_size: int = 1000000,
          accelerated_exploration: bool = True,
          save_models: bool = True,
          load_models: bool = True,
          path_to_actor: str = "./models/sac_actor_carracer_latest",
          path_to_critic: str = "./models/sac_critic_carracer_latest"):
    #TODO T: Implement random restart training
    """
    Training loop. Consists of: 
                                -Setting up environment, agent and memory
                                -loading models (if possible);
                                -training
                                -evaluation (every x episodes)
                                -saving models

    """

    # Environment
    env = gym.make("CarRacing-v0")
    torch.manual_seed(seed)
    np.random.seed(seed)
    env.seed(seed)

    # Agent
    agent = SAC(env.action_space,
                policy = "Gaussian",
                gamma = 0.99,
                tau = 0.005,
                lr = 0.0003,
                alpha = 0.2,
                automatic_temperature_tuning = False,
                batch_size = batch_size,
                hidden_size = 256,
                target_update_interval = 1,
                latent_dim = 32)

    # Memory
    memory = ReplayMemory(replay_size)

    # Training Loop
    total_numsteps = 0
    updates = 0

    # Log Settings and training results
    writer = SummaryWriter(log_dir=log_dir)
    settings_msg = (f"Training SAC for {num_steps} steps"
                    "\nTRAINING SETTINGS:\n"
                    f"Seed={seed}, Batch size: {batch_size}, Updates per step: {updates_per_step}\n"
                    f"Accelerated exploration: {accelerated_exploration}, Start steps: {start_steps}, Replay size: {replay_size}"
                    "\n----------------------------------------------------------------------------------------------------------"
                    "\nALGORITHM SETTINGS:\n"
                    f"Policy: {agent.policy}, Automatic temperature tuning: {agent.automatic_temperature_tuning}\n"
                    f"Gamma: {agent.gamma}, Tau: {agent.tau}, Alpha: {agent.alpha}, LR: {agent.lr}\n"
                    f"Target update interval: {agent.target_update_interval}, Latent dim: {agent.latent_dim}, Hidden size: {agent.hidden_size}")

    logging.info(settings_msg)

    if load_models:
        try:
            agent.load_model(path_to_actor, path_to_critic)
        except FileNotFoundError:
            print("Could not find models. Starting training without models:")

    for i_episode in itertools.count(1):
        episode_reward = 0
        episode_steps = 0
        done = False
        state = env.reset()
        state = process_observation(state)
        state = encoder.sample(state)

        while not done:
            if start_steps > total_numsteps:
                action = env.action_space.sample()  # Sample random action
            else:
                action = agent.select_action(state)  # Sample action from policy

            if len(memory) > batch_size:
                # Number of updates per step in environment
                for _ in range(updates_per_step):
                    # Update parameters of all the networks
                    critic_1_loss, critic_2_loss, policy_loss, ent_loss, alpha = agent.update_parameters(memory, batch_size,updates)
                    writer.add_scalar('loss/critic_1', critic_1_loss, updates)
                    writer.add_scalar('loss/critic_2', critic_2_loss, updates)
                    writer.add_scalar('loss/policy', policy_loss, updates)
                    writer.add_scalar('loss/entropy_loss', ent_loss, updates)
                    writer.add_scalar('entropy_temprature/alpha', alpha, updates)
                    updates += 1

            next_state, reward, done, _ = env.step(action)  # Step
            next_state = process_observation(next_state)
            next_state = encoder.sample(next_state)
            episode_steps += 1
            total_numsteps += 1
            episode_reward += reward

            # Ignore the "done" signal if it comes from hitting the time horizon.
            # (https://github.com/openai/spinningup/blob/master/spinup/algos/sac/sac.py)
            mask = 1 if episode_steps == env._max_episode_steps else float(not done)

            memory.push(state, action, reward, next_state, mask)  # Append transition to memory

            state = next_state

        if total_numsteps > num_steps:
            break

        writer.add_scalar('reward/train', episode_reward, i_episode)

        if i_episode % 10 == 0 and eval == True:
            avg_reward = 0.
            episodes = 10

            if save_models: agent.save_model('carracer', 'latest')

            for _ in range(episodes):
                state = env.reset()
                state = process_observation(state)
                state = encoder.sample(state)

                episode_reward = 0
                done = False
                while not done:
                    action = agent.select_action(state, eval=True)

                    next_state, reward, done, _ = env.step(action)
                    next_state = process_observation(next_state)
                    next_state = encoder.sample(next_state)
                    episode_reward += reward

                    state = next_state
                avg_reward += episode_reward
            avg_reward /= episodes

            if save_models: agent.save_model('carracer', 'latest')

            writer.add_scalar('avg_reward/test', avg_reward, i_episode)

    env.close()


if __name__ == "__main__":
    date = datetime.now()
    log_dir=Path(f"runs/{date.year}_TD3_{date.month}_{date.day}_{date.hour}")
    logging.basicConfig(level=logging.INFO, style='$', filename=str(log_dir/"settings.txt"))
    encoder = load_model("/home/timo/Documents/KIT/4SEM/0Praktikum_ML/VAE_weights.pt", vae=True)
    encoder.to(DEVICE)
    train()