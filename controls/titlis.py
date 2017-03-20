import zmq
import subprocess
import logging

logger = logging.getLogger(__name__)


class Titlis(object):

    def __init__(
            self,
            host,
            port=5555,
            photon_energy=[10000, 40000],
            storage_path="."):
        super(Titlis, self).__init__()
        self.host = host
        self.port = port
        self.storage_path = storage_path
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        subprocess.check_call(
            "ssh det@{0} 'python ~/python-controls-high-energy/controls/titlis_server.py &'".format(
            host), shell=True)
        self.socket.connect("tcp://{0}:{1}".format(
            host, port))
        self.setThresholds(photon_energy)

    def send_command(self, method, kwargs):
        dictionary = {
            "method": method,
            "kwargs": kwargs
        }
        self.socket.send_pyobj(dictionary)
        message = self.socket.recv_pyobj()
        logger.debug("got response %s", message)
        return message

    def setThresholds(self, thresholds):
        return self.send_command("setTresholds", {"thresholds": thresholds})

if __name__ == "__main__":
    detector = Titlis("129.129.99.119")
    message = detector.send_command("echo", {"value": "test"})
    print(message)