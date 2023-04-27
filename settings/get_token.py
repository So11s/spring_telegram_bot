from environs import Env

def load_env(str):
    env = Env()
    env.read_env()
    return env(str)
