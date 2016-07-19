########################################################################
# Initialize all needed packages and modules
#
# Author: Maria Buechner
#
# History:
# 20.11.2013: started
#
########################################################################

# Imports
import click
import IPython
import logging.config
import logging

import controls.motors
import controls.eiger
import controls.pilatus
import controls.comet_tube
import controls.scans
import controls.log_config

@click.command()
@click.option("-v", "--verbose", count=True)
@click.option("-s", "--storage_path",
    default="/afs/psi.ch/project/hedpc/raw_data/2016/pilatus/2016.07.19",
    type=click.Path(exists=True))
@click.option("-t", "--threshold",
    default=10000,
    help="detector threshold energy (eV)")
def main(verbose, storage_path, threshold):
    logger = logging.getLogger()
    logging.config.dictConfig(controls.log_config.get_dict(verbose))
    g0trx = controls.motors.Motor("X02DA-BNK-HE:G0_TRX", "g0trx")
    # detector = controls.eiger.Eiger(
        # "129.129.99.99",
        # storage_path=storage_path,
        # photon_energy=threshold
    # )
    detector = controls.pilatus.Pilatus(
        "129.129.99.81",
        storage_path=storage_path,
        photon_energy=threshold
    )
    tube = controls.comet_tube.CometTube()
    IPython.embed()
