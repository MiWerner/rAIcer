import neat
from Utils import PATH_TO_CONFIGS, PATH_TO_RES, make_dir
import datetime
import os
from AITraining.GenomeEvaluator import GenomeEvaluator
import multiprocessing

# number of generations to evolve
N = 1


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
    for genome_id, genome in genomes:
        current_genomes.append((genome_id, genome))
        if len(current_genomes) == 3:
            __eval_genomes(current_genomes, config)
            current_genomes = []

    # if the number of genomes is not a multiple of three run an extra round for the remainge genomes
    if len(current_genomes) > 0:
        __eval_genomes(current_genomes, config)


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

    for track_id in [2]:  # , 2, 3]:
        # TODO start server

        # TODO check if server is ready ( maybe port)
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

            job.start()  # includes socket.connect(). This muss be performed in the new process...
            jobs.append(job)

        # create dict to collect all fitness-values
        result_dict = {}
        for _ in range(len(jobs)):
            result_dict.update(out_q.get())

        # Wait for all processes to terminate
        for job in jobs:
            job.join()

        # close the sockets and kill the server with the last client
        while len(evaluators) > 0:
            e = evaluators[0]
            evaluators.remove(e)
            if len(evaluators) == 0:
                e.socket.send_kill_msg()
                # TODO check sever shutdown totally
            e.socket.close()

        # store fitness-values in the genomes
        for g_id, genome in genomes:
            genome.fitness += result_dict[g_id]


if __name__ == "__main__":
    time_stamp = datetime.datetime.now()
    current_folder = make_dir(os.path.join(PATH_TO_RES, "NEAT-AI", str(time_stamp)))

    neat_config = neat.Config(neat.DefaultGenome,
                              neat.DefaultReproduction,
                              neat.DefaultSpeciesSet,
                              neat.DefaultStagnation,
                              os.path.join(PATH_TO_CONFIGS, "neat_test_config"))
    # TODO update config file

    # create population
    p = neat.Population(config=neat_config)

    # TODO add reporters

    # TODO population class lags of using fitness_criterion min!!
    winner = p.run(fitness_function=fitness_function, n=N)
    print("\nBest genome:\n{!s}".format(winner))

    # TODO evt Plot statistics and so on
    print("finished")
