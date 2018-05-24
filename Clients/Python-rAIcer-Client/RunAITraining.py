from Utils import ARGS
from AITraining import AITrainer


if __name__ == "__main__":
    AITrainer.run_training(num_generations=ARGS.num_gen,
                           path_to_config=ARGS.config,
                           restore=ARGS.restore,
                           restore_folder=ARGS.restore_folder,
                           restore_checkpoint=ARGS.checkpoint_id)


