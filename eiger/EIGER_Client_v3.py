#
# EIGER_Client_v3.py
# Python Client of the EIGER detector with Albula v 3.0.0
#
#
# Author: Zhentian Wang
#
#
# History:
# 01.06.2015: first release
#
#################################################################

#imports
import sys
sys.path.insert(0,"/sls/X02DA/data/e14980/Data20/ALBULA3/dectris/albula/3.2/python")
import dectris.albula
import time
import ConfigParser
import epics
import thread
import matplotlib.pyplot as plt
import scipy.io as sio
import numpy as np
import requests,json
import os.path
sys.path.append("/sls/X02DA/data/e14980/Data20/dectris/python/dectris/albula/")
from eigerclient import DEigerClient


class EIGER:

    def __init__(self):
        "Initialize EIGER"
        config = ConfigParser.ConfigParser()
        config.read('EIGER_parameters.ini')
        sections = config.sections()
        if len(sections) == 0:
            print "[ERROR] Initial file is corrupted. Fix it first!"
            return
        else:
            params = sections[0]
            self.IP = config.get(params, 'IP')
            self.storagePath = config.get(params, 'storagePath')
            self.photonEnergy = int(config.get(params, 'photonEnergy'))
            self.threshold = int(config.get(params, 'thresholdEnergy'))
	
        self.client = DEigerClient(host=self.IP)
        print "Initialize the EIGER"
        self.client.sendDetectorCommand("initialize")
        self.client.setDetectorConfig("auto_summation", 1)
        self.client.setDetectorConfig("ntrigger", 100) #for multiple trigger, set this value more than 1
		#print "Set file starting number to 0"
		#self.client.setDetectorConfig("image_nr_start", 0)
        print "Set energy to " + str(self.photonEnergy) + "eV."
        self.client.setDetectorConfig("photon_energy", self.photonEnergy)
        print "Set threshold energy to " + str(self.threshold) + "eV."
        self.client.setDetectorConfig("threshold_energy", self.threshold)

    def config(self,photonEnergy,threshold):
        "Re-config the energy and the threshold"
        print "Re-initialize the EIGER"
        self.client.sendDetectorCommand("initialize")
        self.client.setDetectorConfig("auto_summation", 1)
        self.client.setDetectorConfig("ntrigger", 100) #for multiple trigger, set this value more than 1
        print "Set energy to " + str(photonEnergy) + "eV."
        self.client.setDetectorConfig("photon_energy", photonEnergy)
        print "Set threshold energy to " + str(threshold) + "eV."
        self.client.setDetectorConfig("threshold_energy", threshold)	

    def snap(self, expTime, pe=None, t=None):
        "Snap one image"
        if pe is not None:
            self.client.setDetectorConfig("photon_energy", pe)
        if t is not None:
            self.client.setDetectorConfig("threshold_energy", t)

        # Not use the internal flat field caliberation data
        self.client.setDetectorConfig("flatfield_correction_applied", 0)
        # Only take one image
        self.client.setDetectorConfig("nimages", 1)
        self.client.setDetectorConfig("trigger_mode", "ints")
        self.client.setDetectorConfig("frame_time", expTime + 0.000020)
        self.client.setDetectorConfig("count_time", expTime)
        if pe is not None:
            print "Detector configured and arming at " + str(pe) + " eV"
        else:
            print "Arming at " + str(self.photonEnergy) + " eV"

        # Arm the detector
        retVal = self.client.sendDetectorCommand("arm")
        if type(retVal) is not dict:
            print "EIGER controll hang and got probably reinitialized"
            sys.exit("EIGER hang")
        sq_id = retVal['sequence id']
        print "sequence id: " + str(sq_id)
        self.client.sendDetectorCommand("trigger")
		#print "trigger!"
        time.sleep(0.2)  # add to avoid troubles
		#print "sleep!"
        self.client.sendDetectorCommand("disarm")
		#print "disarm!"
        print "Image recorded."

    def snap_save(self, expTime, pe=None, t=None):
        "Snap one image"
        if pe is not None:
            self.client.setDetectorConfig("photon_energy", pe)
        if t is not None:
            self.client.setDetectorConfig("threshold_energy", t)

        # Not use the internal flat field caliberation data
        self.client.setDetectorConfig("flatfield_correction_applied", 0)
        # Only take one image
        self.client.setDetectorConfig("nimages", 1)
        self.client.setDetectorConfig("trigger_mode", "ints")
        self.client.setDetectorConfig("frame_time", expTime + 0.000020)
        self.client.setDetectorConfig("count_time", expTime)
        if pe is not None:
            print "Detector configured and arming at " + str(pe) + " eV"
        else:
            print "Arming at " + str(self.photonEnergy) + " eV"

        # Arm the detector
        retVal = self.client.sendDetectorCommand("arm")
        if type(retVal) is not dict:
            print "EIGER controll hang and got probably reinitialized"
            sys.exit("EIGER hang")
        sq_id = retVal['sequence id']
        print "sequence id: " + str(sq_id)
        self.client.sendDetectorCommand("trigger")
        time.sleep(0.2)  # add to avoid troubles
        self.client.sendDetectorCommand("disarm")
        
        #Save the file
        self.save()
        self.save()
        time.sleep(2) 
        #wait the download finish and convert
        flag = True
        while flag:
            if os.path.exists(self.storagePath + "//series_" + str(sq_id) + "_master.h5") and os.path.exists(self.storagePath + "//series_" + str(sq_id) + "_data_000001.h5"):
                flag = False
            time.sleep(2)

        #Convert to mat
        self.convert_to_mat(sq_id)
        #Delete older files
        self.delete()
        print "Image recorded, saved and converted to matlab format."

    def save(self):
        "Save all teh files from the image server to local storage"
        matching = self.client.fileWriterFiles()
        #[self.client.fileWriterSave(fn, storage_path) for fn in matching]
        for fn in matching:
            self.client.fileWriterSave(fn, self.storagePath)

    def delete(self):
        "Delete all files on the server side."
        matching = self.client.fileWriterFiles()
        [self.client.fileWriterFiles(i, method='DELETE') for i in matching]

    def phase_stepping(self, start, end, interval, expTime, pe=None, t=None):
        "Phase stepping with trigger signal"

        # Step 1: Config the detector
        if pe is not None:
            self.client.setDetectorConfig("photon_energy", pe)
        if t is not None:
            self.client.setDetectorConfig("threshold_energy", t)

        # Not use the internal flat field caliberation data
        self.client.setDetectorConfig("flatfield_correction_applied", 0)
        self.client.setDetectorConfig("nimages", 1)
        self.client.setDetectorConfig("trigger_mode", "ints")
        self.client.setDetectorConfig("frame_time", expTime + 0.000020)
        self.client.setDetectorConfig("count_time", expTime)

        if pe is not None:
            print "Arming at " + str(pe) + " eV"
        else:
            print "Arming at " + str(self.photonEnergy) + " eV"

        # Arm the detector
        retVal = self.client.sendDetectorCommand("arm")
        if type(retVal) is not dict:
            print "EIGER control hang and got probably reinitialized"
            sys.exit("EIGER hang")
        sq_id = retVal['sequence id']
        print "sequence id: " + str(sq_id)

        # Step 2: Stepping
        dstep = float(end-start)/interval
        for x in xrange(interval):
            time.sleep(0.2)
            xs = start + x*dstep
            #G0_TRX.mv(xs)
            self.client.sendDetectorCommand("trigger")
	    
        time.sleep(0.2)  # add to avoid troubles
        self.client.sendDetectorCommand("disarm")
        print "Phase stepping finished."
        # Move Piezo to the starting point
        #G0_TRX.mv(start)

    def multiple_exposure(self, interval, expTime, pe=None, t=None):
        "Phase stepping with trigger signal"

        # Step 1: Config the detector
        if pe is not None:
            self.client.setDetectorConfig("photon_energy", pe)
        if t is not None:
            self.client.setDetectorConfig("threshold_energy", t)

        # Not use the internal flat field caliberation data
        self.client.setDetectorConfig("flatfield_correction_applied", 0)
        self.client.setDetectorConfig("nimages", 1)
        self.client.setDetectorConfig("trigger_mode", "ints")
        self.client.setDetectorConfig("frame_time", expTime + 0.000020)
        self.client.setDetectorConfig("count_time", expTime)

        if pe is not None:
            print "Arming at " + str(pe) + " eV"
        else:
            print "Arming at " + str(self.photonEnergy) + " eV"

        # Arm the detector
        retVal = self.client.sendDetectorCommand("arm")
        if type(retVal) is not dict:
            print "EIGER control hang and got probably reinitialized"
            sys.exit("EIGER hang")
        sq_id = retVal['sequence id']
        print "sequence id: " + str(sq_id)

        # Step 2: Stepping
        for x in xrange(interval):
	    time.sleep(0.2)
	    print str(x) + " steps"
            self.client.sendDetectorCommand("trigger")
	    
        time.sleep(0.2)  # add to avoid troubles
        self.client.sendDetectorCommand("disarm")
        print "Scan finished."

    def convert_to_mat(self, file_id):
        "Convert EIGER hdf5 file to matlab file."
        h5cont = dectris.albula.DImageSeries(self.storagePath + "//series_" + str(file_id) + "_master.h5")
        dataset = h5cont[h5cont.first()].data()
        for i in range(h5cont.first(), h5cont.first() + h5cont.size()-1):
            img = h5cont[i+1]
            dat = img.data()
            dataset = np.concatenate((dataset, dat))
        sio.savemat(self.storagePath + "//dat_" + str(file_id) + ".mat", {'img': dataset})
	

