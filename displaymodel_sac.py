import gym
import numpy as np
import itertools
import torch
import logging
from sac.sac import SAC
from sac.replay_memory import ReplayMemory
from perception.utils import load_model, process_observation
from torch.utils.tensorboard import SummaryWriter
import datetime
from perception.generate_AE_data import generate_action

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
"""Set the device globally if a GPU is available."""



def main(seed: int = 69,
          batch_size: int = 256,
          num_steps: int = 1000000,
          updates_per_step: int = 1,
          start_steps: int = 10000,
          replay_size: int = 1000000,
          accelerated_exploration: bool = True,
          save_models: bool = True,
          load_models: bool = True,
          path_to_actor: str = "models/sac_actor_carracer_6_21_13.pt",
          path_to_critic: str = "models/sac_critic_carracer_6_21_13.pt"):
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
                automatic_temperature_tuning = True,
                batch_size = batch_size,
                hidden_size = 256,
                target_update_interval = 1,
                input_dim = 32)

    #load models 
    try:
        agent.load_model(path_to_actor, path_to_critic)
    except FileNotFoundError:
        print("Could not find models")

    for i_episode in range(5):
        # Get initial observation 
        state = env.reset()
        state = process_observation(state)
        state = encoder.sample(state)
        done = False
        for t in range(1000):
            # render the environment at each step
            env.render()
            # move the car using the policy actions
            action = agent.select_action(state, eval=True)
            state, reward, done, _ = env.step(action)
            state = process_observation(state)
            state = encoder.sample(state)


            if done:
                print("Episode finished after {} timesteps".format(t+1))
                break
    # Close the rendering
    env.close()


 

if __name__ == "__main__":
    encoder = load_model("/fzi/ids/michel/no_backup/WeigthsAutoencoder/VAE_weights.pt", vae=True)
    encoder.to(DEVICE)
    main()