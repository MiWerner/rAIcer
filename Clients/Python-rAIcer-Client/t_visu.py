import sys
sys.argv.append("--direc_dist")
sys.argv.append("--speed")
sys.argv.append("--cp_ids")
sys.argv.append("2")
sys.argv.append("--output_mode_2")
sys.argv.append("--restore_folder")
sys.argv.append("E5")

from Utils import PATH_TO_EXPERIMENTS, ARGS, IO_NAMES
import pickle
import os

import neat
from AITraining import visualize

genome = pickle.load(open(os.path.join(PATH_TO_EXPERIMENTS, ARGS.restore_folder, "winner.p"), "rb"))
neat_config = neat.Config(neat.DefaultGenome,
                          neat.DefaultReproduction,
                          neat.DefaultSpeciesSet,
                          neat.DefaultStagnation,
                          os.path.join(PATH_TO_EXPERIMENTS, ARGS.restore_folder, "configfile"))

filename = os.path.join(PATH_TO_EXPERIMENTS, ARGS.restore_folder, "winner_clean")

visualize.draw_net(neat_config, genome, filename=filename, fmt="png", view=False, node_names=IO_NAMES, show_disabled=False, prune_unused=True, show_bias=True, show_weights=True)
