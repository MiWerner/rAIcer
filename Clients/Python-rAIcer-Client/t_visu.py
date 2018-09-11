import sys
sys.argv.append("--direc_dist")
sys.argv.append("--speed")
sys.argv.append("--cp_ids")
sys.argv.append("2")
sys.argv.append("--output_mode_2")
sys.argv.append("--restore_folder")
sys.argv.append("2018-08-28_10-57-12")

from Utils import PATH_TO_SAVINGS, ARGS, IO_NAMES
import pickle
import os

import neat
from AITraining import visualize

genome = pickle.load(open(os.path.join(PATH_TO_SAVINGS, ARGS.restore_folder, "winner.p"), "rb"))
neat_config = neat.Config(neat.DefaultGenome,
                          neat.DefaultReproduction,
                          neat.DefaultSpeciesSet,
                          neat.DefaultStagnation,
                          os.path.join(PATH_TO_SAVINGS, ARGS.restore_folder, "configfile"))

visualize.draw_net(neat_config, genome, view=True, node_names=IO_NAMES, show_disabled=False, prune_unused=True, show_bias=True, show_weights=True)
