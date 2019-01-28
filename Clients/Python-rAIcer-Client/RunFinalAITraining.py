import sys
sys.argv.append("--direc_dist")
sys.argv.append("--speed")
sys.argv.append("--cp_ids")
sys.argv.append("2")
sys.argv.append("--output_mode_2")
sys.argv.append("--num_gen")
sys.argv.append("1000")
sys.argv.append("--config")
sys.argv.append("neat_config_no_hidden_5_features_2")
sys.argv.append("--restore")
sys.argv.append("--restore_folder")
sys.argv.append("2018-10-12_12-51-54")
sys.argv.append("--checkpoint_id")
sys.argv.append("4")

from Utils import ARGS
from AITraining import FinalAITrainer


if __name__ == "__main__":
    FinalAITrainer.run_training(num_generations=ARGS.num_gen,
                                config_filename=ARGS.config,
                                restore=ARGS.restore,
                                restore_folder=ARGS.restore_folder,
                                restore_checkpoint=ARGS.checkpoint_id)


