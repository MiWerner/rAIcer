import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--hv_dists", action="store_true", default=False, help="Enables hv distances features")
parser.add_argument("--diag_dists", action="store_true", default=False, help="Enables diagonal distances features")
parser.add_argument("--speed", action="store_true", default=False, help="Enables speed features")
parser.add_argument("--ballpos", action="store_true", default=False, help="Enables ballpos features")
parser.add_argument("--num_cp", type=int, default=3, help="Sets the number of Checkpoints in feature vector")
parser.add_argument("--config", type=str, default=None, help="filename of the configfile in config folder")
parser.add_argument("--restore", action="store_true", default=None, help="If set the population is restored from the file defined by restore_folder and checkpoint_id")
parser.add_argument("--restore_folder", type=str, default=None, help="folder name of the run to restore")
parser.add_argument("--checkpoint_id", type=int, default=None, help="id of the checkpoint used to restore run")
parser.add_argument("--num_gen", type=int, default=100, help="The number of generations to run")

args = parser.parse_args()

from Utils import update_feature_parameters
update_feature_parameters(hv_dist=args.hv_dists,
                          diag_dist=args.diag_dists,
                          speed=args.speed,
                          ball_pos=args.ballpos,
                          num_cp_features=args.num_cp)

from AITraining import AITrainer
AITrainer.run_training(N=args.num_gen, path_to_config=args.config,
                       restore=args.restore, restore_folder=args.restore_folder, restore_checkpoint=args.checkpoint_id)


