import argparse

from terrain.generation.fractal_perlin import generate_fractal_perlin_noise
from terrain.generation.perlin import generate_perlin_noise

noise_functions = {
    "perlin": generate_perlin_noise,
    "fractal-perlin": generate_fractal_perlin_noise,
}


parser = argparse.ArgumentParser()
parser.add_argument(
    "-n",
    "--noise",
    help=f"Specify the noise algorithm for terrain generation. Default: perlin (currently supported: {','.join(noise_functions.keys())})",
    default="perlin",
)

parser.add_argument(
    "-t",
    "--tree",
    help="Enable trees",
    action="store_true",
    default=False,
)

parser.add_argument(
    "-st",
    "--style-transfer",
    help="Enable neural style-transfer",
    action="store_true",
    default=False,
)
