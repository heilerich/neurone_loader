# This file is part of neurone_loader
# (https://www.github.com/heilerich/neurone_loader)
# Copyright © 2018 Felix Heilmeyer.
# 
# This file contains code originally from export2hdf5
# Created by Andreas Henelius <andreas.henelius@ttl.fi>,
# Finnish Institute of Occupational Health
#
# This code is released under the MIT License
# http://opensource.org/licenses/mit-license.php
# Please see the file LICENSE for details.

"""
This module contains functions for reading data from a
Bittium NeurOne device. This module currently supports
reading of data and events if the data has been recorded
in one session.
"""

import numpy as np
import xml.etree.ElementTree

from os import path
from construct import Struct, Int32sl, Int64ul

from datetime import datetime

def read_neurone_protocol(fpath):
    """
    Read the measurement protocol from an XML file.

    Arguments:
       - fpath : the path to the directory holding the
                 NeurOne measurement (i.e., the
                 directory Protocol.xml and Session.xml
                 files.

    Returns:
       - a dictionary containing (i) the names of the channels
         in the recording and (ii) meta information
         (recording start/stop times, sampling rate).

    {"meta" : <dict with metadata>,
    "channels" : <array with channel names>}
    """

    # Define filename
    fname_protocol = path.join(fpath, "Protocol.xml")
    fname_session = path.join(fpath, "Session.xml")

    # --------------------------------------------------
    # Read the protocol data
    # --------------------------------------------------
    # Define the XML namespace as a shorthand
    ns = {'xmlns': 'http://www.megaemg.com/DataSetGeneralProtocol.xsd'}

    # Get channel names and organise them according to their
    # physical order (InputNumber), which is the order
    # in which the channels are being sampled.
    docroot = xml.etree.ElementTree.parse(fname_protocol).getroot()
    channels = docroot.findall("xmlns:TableInput", namespaces=ns)
    channel_names = ['']*len(channels)

    for i,ch in enumerate(channels):
        channel_names[i] = (int(ch.findall("xmlns:PhysicalInputNumber", namespaces=ns)[0].text), ch.findall("xmlns:Name", namespaces=ns)[0].text)
    channel_names = [i for _,i in sorted(channel_names)]

    # Get the sampling rate
    sampling_rate = int(docroot.findall("xmlns:TableProtocol", namespaces=ns)[0].findall("xmlns:ActualSamplingFrequency", namespaces=ns)[0].text)

    # --------------------------------------------------
    # Read the session data
    # --------------------------------------------------
    # Define the XML namespace as a shorthand
    ns2 = {'xmlns': 'http://www.megaemg.com/DataSetGeneralSession.xsd'}

    # Get channel names and organise them according to their
    # physical order (InputNumber), which is the order
    # in which the channels are being sampled.
    docroot = xml.etree.ElementTree.parse(fname_session).getroot()
    session = docroot.findall("xmlns:TableSession", namespaces=ns2)
    time_start = session[0].findall("xmlns:StartDateTime", namespaces=ns2)[0].text
    time_stop = session[0].findall("xmlns:StopDateTime", namespaces=ns2)[0].text
    phases = [phase.findall("xmlns:Folder", namespaces=ns2)[0].text.split("\\")[-1] for phase in docroot.findall("xmlns:TableSessionPhase", namespaces=ns2)]

    # --------------------------------------------------
    # Package the information
    # --------------------------------------------------
    meta = {}

    tstart = time_start[0:time_start.index('+')]
    tstop = time_stop[0:time_stop.index('+')]

    if (len(tstart) > 26):
        tstart = tstart[0:26]
    if (len(tstop) > 26):
        tstop = tstop[0:26]
        
    meta["time_start"] = datetime.strptime(tstart, "%Y-%m-%dT%H:%M:%S.%f")
    meta["time_stop"] = datetime.strptime(tstop, "%Y-%m-%dT%H:%M:%S.%f")
    meta["sampling_rate"] = sampling_rate

    return {'channels' : channel_names, 'meta' : meta, 'phases': phases}


def read_neurone_data(fpath, session_phase = 1, protocol = None):
    """
    Read the NeurOne signal data from a binary file.

    Arguments:
       - fpath : the path to the directory holding the
                 NeurOne measurement (i.e., the
                 directory Protocol.xml and Session.xml
                 files.

       - session_phase :
                 The phase of the measurement. Currently
                 only reading of the first phase (1) is
                 supported.

       - protocol :
                  The dictionary obtained using the function
                  read_neurone_protocol. This argument is optional
                  and if not given, the protocol is automatically read.
                    
    Returns:
       - A numpy ndarray with the data, where each columns stores
         the data for one channel.
    """

    fname = path.join(fpath, str(session_phase), '1.bin')

    # Read the protocol unless provided
    if protocol is None:
        protocol = read_neurone_protocol(fpath)
    
    # Determine number of samples to read
    f_info = path.getsize(fname)
    n_channels = len(protocol['channels'])
    n_samples = int(f_info / 4 / n_channels)

    # Read the data and store the data
    # in an ndarray
    with open(fname, mode='rb') as file:
        data = np.fromfile(fname, dtype='<i4')
        data.shape = (n_samples, n_channels)

    return data


def get_n1_event_format():
    """
    Define the format for the events in a neurone recording.
    
    Arguments: None.

    Returns:
       - A Struct (from the construct library) describing the
         event format.
    """

    # Define the data format of the events
    return Struct(
        "Revision"          / Int32sl,
        "RFU1"              / Int32sl,
        "Type"              / Int32sl,
        "SourcePort"        / Int32sl,
        "ChannelNumber"     / Int32sl,
        "Code"              / Int32sl,
        "StartSampleIndex"  / Int64ul,
        "StopSampleIndex"   / Int64ul,
        "DescriptionLength" / Int64ul,
        "DescriptionOffset" / Int64ul,
        "DataLength"        / Int64ul,
        "DataOffset"        / Int64ul,
        "RFU2"              / Int32sl,
        "RFU3"              / Int32sl,
        "RFU4"              / Int32sl,
        "RFU5"              / Int32sl)


def read_neurone_events(fpath, session_phase = 1, sampling_rate = None):
    """
    Read the NeurOne events from a binary file.

    Arguments:
       - fpath : the path to the directory holding the
                 NeurOne measurement (i.e., the
                 directory Protocol.xml and Session.xml
                 files.

       - sampling_rate :
                 The sampling rate of the recording.
                 This argument is optional and if not given,
                 the protocol is automatically read.

       - session_phase :
                 The phase of the measurement. Currently
                 only reading of the first phase (1) is
                 supported.

    Returns:
       - A dict containing the events and the data type for the events.
    {"events" : <numpy structured array with the events>,
    "events_dtype" : <array with the numpy dtype for the events>}
    """

    fname = path.join(fpath, str(session_phase), "events.bin")

    # Get the sampling rate unless provided
    if sampling_rate is None:
        protocol = read_neurone_protocol(fpath)
        sampling_rate = protocol['meta']['sampling_rate']
    
    # Determine number of events
    f_info = path.getsize(fname)
    n_events = int(f_info / 88)
    events = [''] * n_events

    # Read events in chunks of 88 bytes and unpack
    # also add start / stop time for each event
    # and remove 'reserved for future use' (RFU) fields
    format = get_n1_event_format()
    with open(fname, mode='rb') as file:
        for i in range(n_events):
            events[i] = format.parse(file.read(88))
            events[i]['StartTime'] = events[i]['StartSampleIndex'] / sampling_rate
            events[i]['StopTime'] = events[i]['StopSampleIndex'] / sampling_rate
            for j in range(5):
                del events[i]['RFU' + str(j+1)]
            del events[i]['_io']

    # Create a numpy structured array from the events
    events_dtype = np.dtype([("Revision"          , np.int32),
                             ("Type"              , np.int32),
                             ("SourcePort"        , np.int32),
                             ("ChannelNumber"     , np.int32),
                             ("Code"              , np.int32),
                             ("StartSampleIndex"  , np.int64),
                             ("StopSampleIndex"   , np.int64),
                             ("DescriptionLength" , np.int64),
                             ("DescriptionOffset" , np.int64),
                             ("DataLength"        , np.int64),
                             ("DataOffset"        , np.int64),
                             ("StartTime"         , np.int64),
                             ("StopTime"          , np.int64) ])

    # convert array of event dicts to an array of tuples
    if len(events) == 0:
        return {'events': [], 'dtype': []}
    keylist = [k for k, v in events[0].items()]
    tmp =  [tuple([e[k] for k in keylist]) for e in events]
    events = np.array(tmp, dtype = events_dtype)

    return {'events' : events, 'dtype' : events_dtype}


def write_neurone_events(fname, events):
    """
    Write neurone events.

    Arguments:
       - fname : the file to write the events to (will be overwritten)

       - events : an array of dicts, each dict containing one event.
         Each event has the following fields (here with example data):
              Revision = 5
              Type = 4
              SourcePort = 3
              ChannelNumber = 0
              Code = 2
              StartSampleIndex = 224042
              StopSampleIndex = 224042
              DescriptionLength = 0
              DescriptionOffset = 0
              DataLength = 0
              DataOffset = 0

              Note that fields RFU0 to RFU5 are automatically added.

    Returns:
       - nothing
    """

    format = get_n1_event_format()

    with open(fname, mode='wb') as file:
        for e in events:
            for j in range(5):
                e['RFU' + str(j+1)] = 0
                file.write(format.build(e))


def read_neurone(fpath):
    """
    Read the neurone data.

    Arguments:
       - fpath : the path to the directory holding the
                 NeurOne measurement (i.e., the
                 directory Protocol.xml and Session.xml
                 files.
    Returns:
       - a dictionary containing the data, events and the
         data type (numpy dtype) for the events.

    {"data" : <the signal data>,
    "events" : <the events>,
    "events_dtype" : <event data type>}
    """

    # Read the protocol
    protocol = read_neurone_protocol(fpath)

    # Read the signal data
    data = read_neurone_data(fpath, session_phase = 1, protocol = protocol)

    # Read the events
    events = read_neurone_events(fpath, session_phase = 1, sampling_rate = float(protocol['meta']['sampling_rate']))

    # Create a time vector
    timevec = np.array(range(data.shape[0])) / float(protocol['meta']['sampling_rate'])

    out = [0] * len(protocol["channels"])
    for i, label in enumerate(protocol["channels"]):
        data_out =  {}
        data_out[label] = data[:,i]
        data_out["time"] = timevec
        out[i] = {"meta" : protocol["meta"], "data" : data_out}

    return {"data" : out, "events" : events['events'], "events_dtype" : events['dtype']}

def read_neurone_data_hdf5(fpath):
    """
    Read the neurone data in a format compatible with the
    HDF5-exporting function export_hdf5.

    Arguments:
       - fpath : the path to the directory holding the
                 NeurOne measurement (i.e., the
                 directory Protocol.xml and Session.xml
                 files.
    Returns:
       - a list of dictionaries, where each dictionary
         represents a feature as a time series ("signal")
    {"meta" : <dict with metadata>,
    "data" : {"time" : [...], "<channelname" : [...] }}
    """

    # Read the protocol
    protocol = read_neurone_protocol(fpath)

    # Read the signal data
    data = read_neurone_data(fpath, session_phase = 1, protocol = protocol)

    # Create a time vector
    timevec = np.array(range(data.shape[0])) / float(protocol['meta']['sampling_rate'])

    out = [0] * len(protocol["channels"])
    for i, label in enumerate(protocol["channels"]):
        data_out =  {}
        data_out[label] = data[:,i]
        data_out["time"] = timevec
        out[i] = {"meta" : protocol["meta"], "data" : data_out}

    return out

def read_neurone_events_hdf5(fpath):
    """
    Read the neurone events in a format compatible with the
    HDF5-exporting function export_hdf5.

    Arguments:
       - fpath : the path to the directory holding the
                 NeurOne measurement (i.e., the
                 directory Protocol.xml and Session.xml
                 files.
    Returns:
       - A dict containing the events and the data type for the events.

    {"events" : <numpy structured array with the events>,
    "events_dtype" : <array with the numpy dtype for the events>}
    """

    # Read the protocol
    protocol = read_neurone_protocol(fpath)

    # Read the signal data
    data = read_neurone_data(fpath, session_phase = 1, protocol = protocol)

    # Read the events
    events = read_neurone_events(fpath, session_phase = 1, sampling_rate = float(protocol['meta']['sampling_rate']))

    return events
