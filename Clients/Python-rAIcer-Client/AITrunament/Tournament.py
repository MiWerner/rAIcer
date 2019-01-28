import pickle
import os
from Utils import PATH_TO_EXPERIMENTS, ARGS, is_windows, start_server
import neat
import multiprocessing
from AITrunament.TournamentClient import TournamentClient

ki_folders = [
    "E1", "E2", "E3", "E4", "E5",
]

cp_ids = [[1], [2], [2], [2], [2, 4]]

output_mode_2 = [False, False, True, True, True]

results = open("results.txt", "a")

for id_home in [1]:
    for id_guest in [3]:
        if id_home == 3 and id_guest == 3:
            continue

        # restore clients
        genome_home = pickle.load(open(os.path.join(PATH_TO_EXPERIMENTS, ki_folders[id_home], "winner.p"), "rb"))
        neat_config_home = neat.Config(neat.DefaultGenome,
                                  neat.DefaultReproduction,
                                  neat.DefaultSpeciesSet,
                                  neat.DefaultStagnation,
                                  os.path.join(PATH_TO_EXPERIMENTS, ki_folders[id_home], "configfile"))

        net_home = neat.nn.FeedForwardNetwork.create(genome=genome_home, config=neat_config_home)

        genome_guest = pickle.load(open(os.path.join(PATH_TO_EXPERIMENTS, ki_folders[id_guest], "winner.p"), "rb"))
        neat_config_guest = neat.Config(neat.DefaultGenome,
                                       neat.DefaultReproduction,
                                       neat.DefaultSpeciesSet,
                                       neat.DefaultStagnation,
                                       os.path.join(PATH_TO_EXPERIMENTS, ki_folders[id_guest], "configfile"))

        net_guest = neat.nn.FeedForwardNetwork.create(genome=genome_guest, config=neat_config_guest)

        for track_id in [3]:  # 1 , 2, 3]:

            # start server
            server = start_server()
            if not is_windows:
                server.daemon = True
                server.start()

            # create Queue for storing the fitness-values of each genome, to get them from the created processes
            out_q = multiprocessing.Queue()

            # create and a new process for each genome
            # a process includes the connection-handling to the server and the client-logic of the corresponding genome
            jobs = []
            clients = []
            if id_home == id_guest:
                client_home = TournamentClient(cp_ids[id_home], output_mode_2[id_home])
                clients.append(client_home)
                job_home = multiprocessing.Process(target=client_home.run, args=(id_home, net_home, out_q, 1, track_id))
                job_home.start()
                jobs.append(job_home)
            else:
                client_home = TournamentClient(cp_ids[id_home], output_mode_2[id_home])
                client_guest = TournamentClient(cp_ids[id_guest], output_mode_2[id_guest])
                clients.append(client_home)
                clients.append(client_guest)

                job_home = multiprocessing.Process(target=client_home.run, args=(id_home, net_home, out_q, 2, track_id))
                job_guest = multiprocessing.Process(target=client_guest.run, args=(id_guest, net_guest, out_q, 2, track_id))

                job_home.start()
                job_guest.start()

                jobs.append(job_home)
                jobs.append(job_guest)

            # create dict to collect all fitness-values
            result_dict = {}
            for _ in range(len(jobs)):
                result_dict.update(out_q.get())

            # Wait for all processes to terminate
            for job in jobs:
                job.join()
                pass

            for c in clients:
                c.socket.is_active = False
                if not is_windows:
                    pass
#                    c.socket.send_kill_msg()

            # Wait for server shutdown
            if is_windows:
                server.terminate()
            else:
                server.join()

            # ensure sockets are closed
            for c in clients:
                try:
                    c.socket.close()
                except ConnectionResetError:
                    pass

            results.write("{0} vs. {1} at track {2}: \n   {0}: {3} \n   {1}: {4}\n~~~~~~~~~~~~~~~~~~~".format(id_home, id_guest, track_id, result_dict[id_home], result_dict[id_guest]))
            print("{0} vs. {1} at track {2}: \n   {0}: {3} \n   {1}: {4}\n~~~~~~~~~~~~~~~~~~~".format(id_home, id_guest, track_id,
                                                                                         result_dict[id_home],
                                                                                         result_dict[id_guest]))
