import Utils
import time
import subprocess
import multiprocessing
import RaicerSocket


class Client:

    def __init__(self):
        self.socket = RaicerSocket.RaicerSocket()

    def connect_to_server(self):
        t = time.time() + 100
        while time.time() <= t:
            try:
                self.socket.connect()

                client_id = None
                while client_id in [None, -1]:
                    client_id, *_ = self.socket.receive()
                    time.sleep(.1)
                print("ID: ", client_id)
                if client_id == 3:
                    # if current id is the largest possible, this client is the last one and should start the game
                    self.socket.send_setting_msg(track_id=1, num_laps=1)
                time.sleep(10)

                return True
            except ConnectionRefusedError:
                time.sleep(.5)
        return False


if __name__ == '__main__':
    # Start server
    print(Utils.PATH_TO_WINDOWS_CUSTOM_SERVER)
    server = subprocess.Popen([Utils.PATH_TO_WINDOWS_CUSTOM_SERVER])

    # Start clients
    jobs = []
    clients = []
    for i in range(0, 3):
        c = Client()
        clients.append(c)

        job = multiprocessing.Process(target=c.connect_to_server, args=())
        jobs.append(job)
        job.start()

    # Wait for all processes to terminate
    for job in jobs:
        job.join()

    # Stop server
    time.sleep(5)
    server.terminate()
