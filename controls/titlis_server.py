import dectris
import dectris.spluegen
import dectris.albula
import os
import numpy
import time
import zmq
import logging
import glob
from PIL import Image

logger = logging.getLogger(__name__)


class TitlisServer(object):

    """zmq REP server to remotely control the titlis detector."""

    def __init__(self):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind("tcp://*:5555")
        file_name_template = "titlis_ev_{event_id}_seq_{sequence_id}_th_{threshold_id}_im_{image_id}"
        file_name_template_suffix = "tif"
        self.number_of_thresholds = 2

        # # Detector Calibration File
        calibration_path = "/home/det/calibration/calibration-T0804_75-01_20170314_14h29m22/"

        # Detector Configuration File
        configuration_file = "/etc/dectris/titlis-75um_500k-MatH.py"

        # Create Spluegen Camera Object
        self.camera = dectris.spluegen.DCamera(
            "10.0.10.50",
            configuration_file=configuration_file
        )
        self.camera.open()
        self.camera.setNumberOfThresholds(self.number_of_thresholds)
        self.camera.setCalibrationPath(calibration_path)

        # Fetch the Detector and Logger Objects
        self.detector = self.camera.getDetectorObject()
        self.image_builder = self.camera._image_builder
        self.image_builder._file_name_template = file_name_template
        self.image_builder._file_name_suffix = "tif"
        self.setNTrigger(1)

    def setNTrigger(self, n):
        self.n_trigger = n
        # Set the Detector Image Series Parameter(s)
        self.detector.setImageSeriesParameters(
            series_id=1,
            number_of_triggers=n,
            number_of_images=1,
            number_of_thresholds=self.number_of_thresholds)
        # Set the Image Destination and the File Name Template
        basepath = "/data/slow_acquisition/"
        self.image_destination_path = os.path.join(
            basepath,
            time.strftime("%y%m%d.%H%M%S%f"))
        if not os.path.exists(self.image_destination_path):
            os.makedirs(self.image_destination_path)
        self.image_builder.setSaveDirectory(self.image_destination_path)
        return n

    def trigger(self, exposure_time=1):
        self.detector.setExposureParameters(
            count_time=exposure_time,
            image_period=1.01 * exposure_time,
            sequence_period=1.02 * exposure_time,
            frame_count_time=1.01 * exposure_time)
        self.detector.sendSoftwareTriggerPulse()
        saved = self.image_builder.waitImageIsSaved()
        return saved

    def loop(self):
        while True:
            message = self.socket.recv_pyobj()
            method_name = message["method"]
            if method_name == "__exit__": break
            args = message["args"]
            kwargs = message["kwargs"]
            logger.debug("received %s", method_name)
            logger.debug("args %s", args)
            logger.debug("kwargs %s", kwargs)
            try:
                value = getattr(self, method_name)(*args, **kwargs)
                self.socket.send_pyobj({
                    "status": 200,
                    "value": value})
            except Exception as e:
                self.socket.send_pyobj({
                    "status": 500,
                    "value": e.message})

    def echo(self, value):
        return value

    def arm(self):
        value = self.detector.arm("ints")
        time.sleep(1)
        return value

    def disarm(self):
        return self.detector.disarmSeries()

    def setTresholds(thresholds):
        assert len(thresholds) == 2
        return self.camera.setEnergyForReal(
            80000, # fudge useless value
            threshold=thresholds[0],
            threshold2=thresholds[1])

    def save(self):
        output_file_name = self.image_destination_path + ".h5"
        output_file = h5py.File(output_file_name)
        groups = ["th_0", "th_1"]
        for group_name in group:
            group = output_file.require_group("/entry/data/{0}".format(group_name))
            group_files = glob.glob(
                os.path.join(
                    self.image_destination_path,
                    "*{0}*.tif".format(group_name)))
            for i, group_file in enumerate(group_files):
                dataset = np.array(Image.open(group_file))
                group.create_dataset(
                    "data_{0:06d}".format(i + 1),
                    data=dataset)
                os.remove(group_file)
        output_file.close()
        logger.debug("created %s file", output_file_name)
        return os.path.abspath(output_file_name)



if __name__ == "__main__":
    LOG_FILENAME = 'example.log'
    FORMAT = '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
    logging.basicConfig(
        format=FORMAT,
        filename=LOG_FILENAME,
        level=logging.DEBUG,
    )
    logger.debug("starting server")
    server = TitlisServer()
    logger.debug("starting loop")
    server.loop()
