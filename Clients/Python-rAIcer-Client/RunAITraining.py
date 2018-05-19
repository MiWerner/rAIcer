import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--hv_dists", action="store_true", default=False, help="Enables hv distances features")
parser.add_argument("--diag_dists", action="store_true", default=False, help="Enables diagonal distances features")
parser.add_argument("--speed", action="store_true", default=False, help="Enables speed features")
parser.add_argument("--ballpos", action="store_true", default=False, help="Enables ballpos features")
parser.add_argument("--num_cp", type=int, default=3, help="Sets the number of Checkpoints in feature vector")
parser.add_argument("--config", type=str, default=None, help="Path to the configfile")
parser.add_argument("--restore", type=str, default=None, help="If given the population is restored from the given file")
parser.add_argument("--num_gen", type=int, default=100, help="The number of generations to run")

args = parser.parse_args()

from Utils import update_feature_parameters
update_feature_parameters(hv_dist=args.hv_dists,
                          diag_dist=args.diag_dists,
                          speed=args.speed,
                          ball_pos=args.ballpos,
                          num_cp_features=args.num_cp)

from AITraining import AITrainer
AITrainer.run_training(N=args.num_gen, path_to_config=args.config, path_to_restore=args.restore)


