import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--hv_dists", action="store_true", default=False, help="Enables hv distances features")
parser.add_argument("--diag_dists", action="store_true", default=False, help="Enables diagonal distances features")
parser.add_argument("--speed", action="store_true", default=False, help="Enables speed features")
parser.add_argument("--ballpos", action="store_true", default=False, help="Enables ballpos features")
parser.add_argument("--num_cp", type=int, default=3, help="Sets the number of Checkpoints in feature vector")

args = parser.parse_args()

from Utils import update_feature_parameters
update_feature_parameters(hv_dist=args.hv_dists,
                          diag_dist=args.diag_dists,
                          speed=args.speed,
                          ball_pos=args.ballpos,
                          num_cp_features=args.num_cp)

from AITraining import AITrainer
AITrainer.run_training()


