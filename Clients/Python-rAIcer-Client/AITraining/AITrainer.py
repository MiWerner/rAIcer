import neat
import datetime
import os
from AITraining.GenomeEvaluator import GenomeEvaluator
import multiprocessing
from Utils import PATH_TO_CONFIGS, PATH_TO_RES, make_dir, start_server
from AITraining import visualize
import pickle
import sys


def fitness_function(genomes, config):
    """
    Calculates the fitness-value for each genome of the current generation.
    There for each genome is tested on the server
    :param genomes: list of tuples with format (genome_id, genome) representing all genomes of a generation
    :param config: the current configuration
    :return:
    """
    current_genomes = []

    # group three genomes and evaluate them in the same game
    min_g_id = 1
    max_g_id = 3
    for genome_id, genome in genomes:
        current_genomes.append((genome_id, genome))
        if len(current_genomes) == 3:
            sys.stdout.write("\rGenomes {} to {} of {} are in evaluation now ..."
                             .format(min_g_id, max_g_id, len(genomes)))
            sys.stdout.flush()
            __eval_genomes(current_genomes, config)
            current_genomes = []
            min_g_id += 3
            max_g_id += 3

    # if the number of genomes is not a multiple of three run an extra round for the remaining genomes
    if len(current_genomes) > 0:
        sys.stdout.write("\rGenomes {} to {} of {} are in evaluation now ..."
                         .format(min_g_id, len(genomes), len(genomes)))
        sys.stdout.flush()
        __eval_genomes(current_genomes, config)
    print("")


def __eval_genomes(genomes, config):
    """
    Runs the evaluation for the given genomes.
    For each genome a new process is started, which runs the genome as a client.
    After finishing the game the fitness-value is stored in genome.fitness .
    Note that the server only can handle three clients maximum at once.
    :param genomes: list of tuples with format (genome_id, genome) representing all genomes evaluated together
    :param config: the current configuration
    :return:
    """
    for g_id, genome in genomes:
        genome.fitness = 0

    for track_id in [1]:  # , 2, 3]:

        # start server
        server = start_server()
        server.daemon = True
        server.start()

        # create Queue for storing the fitness-values of each genome, to get them from the created processes
        out_q = multiprocessing.Queue()

        # create and a new process for each genome
        # a process includes the connection-handling to the server and the client-logic of the corresponding genome
        jobs = []
        evaluators = []
        for g_id, genome in genomes:
            e = GenomeEvaluator()
            evaluators.append(e)
            job = multiprocessing.Process(target=e.run,
                                          args=(g_id, genome, config, out_q, len(genomes), track_id))

            job.start()  # includes socket.connect() and start of game. This muss be performed in the new process...
            jobs.append(job)

        # create dict to collect all fitness-values
        result_dict = {}
        for _ in range(len(jobs)):
            result_dict.update(out_q.get())

        # Wait for all processes to terminate
        for job in jobs:
            job.join()

        for e in evaluators:
            e.socket.is_active = False
            e.socket.send_kill_msg()

        # Wait for server shutdown
        server.join()

        # ensure sockets are closed
        for e in evaluators:
            try:
                e.socket.close()
            except ConnectionResetError:
                pass

        # store fitness-values in the genomes
        for g_id, genome in genomes:
            genome.fitness += result_dict[g_id]


def run_training(N, path_to_config=None, path_to_restore=None):
    from Utils import IO_NAMES

    if path_to_config is None:
        path_to_config = os.path.join(PATH_TO_CONFIGS, "neat_test_config")

    neat_config = neat.Config(neat.DefaultGenome,
                              neat.DefaultReproduction,
                              neat.DefaultSpeciesSet,
                              neat.DefaultStagnation,
                              path_to_config)

    # create population
    if path_to_restore is None:
        time_stamp = datetime.datetime.now()
        current_folder = make_dir(os.path.join(PATH_TO_RES, "NEAT-AI", str(time_stamp).split(":")[0]))

        p = neat.Population(config=neat_config)
    else:
        p = neat.Checkpointer.restore_checkpoint(path_to_restore)
        current_folder = os.path.join(path_to_restore, os.pardir)

    # show progress on the console
    p.add_reporter(neat.StdOutReporter(True))

    # Create Reporter saving statistics over the generations and to get the best genome
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    # Create reporter to save state during the evolution
    p.add_reporter(neat.Checkpointer(filename_prefix=os.path.join(current_folder, "checkpoints", "checkpoint-")))

    for gen in range(N):
        try:
            current_best = p.run(fitness_function=fitness_function, n=N)

            # save visualisation of winner
            visualize.draw_net(config=neat_config, genome=current_best, node_names=IO_NAMES, view=False,
                               filename=os.path.join(current_folder, "checkpoints", "checkpoint-{}-best".format(gen)),
                               fmt="svg")

            # save winner for later use
            pickle.dump(current_best,
                        open(os.path.join(current_folder, "checkpoints", "checkpoint-{}-best".format(gen)), "wb"))

        except Exception as err:
            print(err)

    # save visualisation of winner and statistics
    print("\nBest genome:\n{!s}".format(current_best))
    visualize.draw_net(config=neat_config, genome=current_best, node_names=IO_NAMES, view=False,
                       filename=os.path.join(current_folder, "checkpoints", "checkpint-{}-best".format(gen)),
                       fmt="svg")

    # save winner for later use
    pickle.dump(current_best,
                open(os.path.join(current_folder, "checkpoints", "checkpoint-{}-best".format(gen)), "wb"))

    visualize.plot_stats(stats, ylog=False, view=False, filename=os.path.join(current_folder, 'avg_fitness.svg'))
    visualize.plot_species(stats, view=False, filename=os.path.join(current_folder, 'speciation.svg'))

    print("finished")
