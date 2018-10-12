from Utils import ARGS
from AITraining import FinalAITrainer


if __name__ == "__main__":
    FinalAITrainer.run_training(num_generations=ARGS.num_gen,
                                config_filename=ARGS.config,
                                restore=ARGS.restore,
                                restore_folder=ARGS.restore_folder,
                                restore_checkpoint=ARGS.checkpoint_id)


