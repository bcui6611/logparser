#!/usr/bin/env python2.7
# -*- mode: Python;-*-

import cStringIO
import zipfile
import tarfile
import inspect
import os.path
import re
import argparse
import logging
import threading
import signal
import time
import datetime
import calendar
import string
import sys
import multiprocessing
import pprint
from Queue import Full

from os import _exit
from os import walk
from io import TextIOWrapper

import cProfile, pstats, StringIO

import globals
import erlangParser

""" This is the top level file for running LogParser.  It is responsible for loading the data
    and starting the the web server.  The program relies on three other python files:-
    1) globals.py - contains the globals variables used by logparser
"""

def argumentParsing():
    parser = argparse.ArgumentParser(description='LogParser')
    parser.add_argument(
        '-d', '--dir', default='.', help='Directory to search for collectinfo .zips')
    parser.add_argument('-v', '--debug', action='store_true',
                        default=False, help='Enable debugging messages')
    parser.add_argument('--version',  action='store_true',
                        default=False, help='Prints out the version number of logparser')

    return parser.parse_args()


def num(s):
    """ Simple function for converting a string to an int or float.
        It is used by the stats_kv function (see below). """
    try:
        return int(s)
    except ValueError:
        try:
            return float(s)
        except ValueError:
            print('Error num is not an int or float, see num(s). s = ' + s)
            os._exit(1)

def stats_kv(line, kvdictionary):
    matchObj = re.match(r'([^\s]+)\s+(.*)$', line, re.I)
    if matchObj:
        key = matchObj.group(1)
        value = matchObj.group(2)
        matchObj = re.match(r'[\-\d]+(.\d+)?$', value, re.I)
        if matchObj:
            value = num(value)
            kvdictionary[key] = value

def isStatsForBucket(line):
    matchObj = re.match(
        r'^\[stats:debug,([^,]+),ns_1@([^:]+):.*Stats for bucket \"(.*)\".*$', line, re.M | re.I)
    if matchObj:
        dayandtime = matchObj.group(1)
        node = matchObj.group(2)
        bucket = matchObj.group(3)
        formatteddayandtime = datetime.datetime.strptime(
            dayandtime, '%Y-%m-%dT%H:%M:%S.%f')
        epochtime = calendar.timegm(formatteddayandtime.timetuple())
        return bucket, epochtime, node
    else:
        return "", 0, ""

def isNsDoctorStats(line):
    matchObj = re.match(r'^\[ns_doctor:debug,([^,]+),ns_1@([^:]+):ns_doc[^\[]+(.*$)', line)
    if matchObj:
        dayandtime = matchObj.group(1)
        node = matchObj.group(2)
        head = matchObj.group(3)
        formatteddayandtime = datetime.datetime.strptime(
            dayandtime, '%Y-%m-%dT%H:%M:%S.%f')
        epochtime = calendar.timegm(formatteddayandtime.timetuple())
        return node, epochtime, head
    else:
        return "",0, ""

def isLogEvent(line):
    matchObj = re.match(
        r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}.\d{3})\s.*\(ns_1@([^\)]+).*\s-\s(.*)$', line, re.M | re.I)
    if matchObj:
        dayandtime = matchObj.group(1)
        node = matchObj.group(2)
        event = matchObj.group(3)
        formatteddayandtime = datetime.datetime.strptime(
            dayandtime, '%Y-%m-%d %H:%M:%S.%f')
        epochtime = calendar.timegm(formatteddayandtime.timetuple())
        return epochtime, node, event
    else:
        return 0, "", ""


def stats_parse(bucketDictionary, zipfile, stats_file, filename, progress_queue):
    try:
        with tarfile.open(stats_file, mode='r:gz') as tf:
            bucket = None
            statsDictionary = None
            t = time.clock()
            begin_stats = False
            doctor_start = False
            doctor_bucket = "@doctor"
            event_bucket = "@event"
            bucketDictionary[doctor_bucket] = []
            bucketDictionary[event_bucket] = []
            for entry in tf.getnames():
                for line in tf.extractfile(entry):
                    line = line.rstrip().lstrip()
                    if line != "":
                        if begin_stats:
                            if bucket:
                                # Add to statsDictionary
                                stats_kv(line, statsDictionary)
                        elif doctor_start:
                            doctor_data = doctor_data + line
                            if line.endswith("]}]}]\n"):
                                doctor_start = False
                                doctor_stats = erlangParser.parseErlangConfig(doctor_data)

                                for key in doctor_stats:
                                    doctor_stats[key]['host'] = key
                                    doctor_stats[key]['localtime'] = statsDictionary['localtime']
                                    doctor_stats[key]['node'] = statsDictionary['node']
                                    bucketDictionary.get(doctor_bucket).append(doctor_stats[key])
                        else:
                            #check stats for buckets
                            (possibleBucket, epoch, node) = isStatsForBucket(line)
                            if epoch != 0:
                                begin_stats = True
                                bucket = possibleBucket
                                statsDictionary = dict()
                                statsDictionary['localtime'] = epoch
                                statsDictionary['node'] = node
                                # check if have previous stats for this bucket
                                if bucket not in bucketDictionary.keys():
                                    bucketDictionary[bucket] = []
                            else:
                                #check event
                                (epoch, node, event) = isLogEvent(line)
                                if epoch != 0:
                                    eventDict = dict()
                                    eventDict['localtime'] = epoch
                                    eventDict['node'] = node
                                    eventDict['event'] = event
                                    bucketDictionary.get(event_bucket).append(eventDict)
                                    bucket = None
                                else:
                                    #check doctor stats
                                    (node, epoch, head) = isNsDoctorStats(line)
                                    if epoch != 0:
                                        if not doctor_start:
                                            doctor_start = True
                                            statsDictionary = dict()
                                            statsDictionary['localtime'] = epoch
                                            statsDictionary['node'] = node
                                            doctor_data = head + "\n"
                                        else:
                                            logging.error("unfinished line:" + doctor_data)
                    else:
                        if begin_stats:
                            # reached an empty line
                            begin_stats = False
                            if bucket:
                                #print bucket
                                bucketDictionary.get(bucket).append(statsDictionary)
                            bucket = None
                        elif doctor_start:
                            doctor_start = False
                            doctor_stats = erlangParser.parseErlangConfig(doctor_data)

                            for key in doctor_stats:
                                doctor_stats[key]['host'] = key
                                doctor_stats[key]['localtime'] = statsDictionary['localtime']
                                doctor_stats[key]['node'] = statsDictionary['node']
                                bucketDictionary.get(doctor_bucket).append(doctor_stats[key])

            process_time = time.clock() - t
            print "{}: Processing of stats took {} seconds".format(filename, process_time) 
    except KeyError:
        logging.error('Error: Cannot find log in' + stats_file + \
                      'See stats_parse(bucketDictionary, tarfile, stats_file, filename).')
        os._exit(1)


def untar(file):
    tfile = tarfile.open(file, 'r:gz')
    tfile.extractall()
    tfile.close()

def output_logfile(stats_file, bucketDictionary):
    logfilename = stats_file + ".log"
    with open(logfilename, 'w') as out_file:
        for bucket, stats_kv in bucketDictionary.iteritems():
            for event in stats_kv:
                if 'localtime' not in event.keys():
                    continue
                strbuf = cStringIO.StringIO()
                tmstamp = datetime.datetime.fromtimestamp(event['localtime']).strftime('%Y-%m-%d %H:%M:%S')
                strbuf.write("[%s] bucket=%s " % (tmstamp, bucket))
                for k, v in event.iteritems():
                    strbuf.write("%s=%s " % (k, v))

                #print content
                out_file.write("%s\n" % strbuf.getvalue())
                strbuf.close()

def load_collectinfo(filename, args, progress_queue, process_stats_queue):
    """The function is invoked by each thread responsible for loading
        a tar file. """
    # First open the zipfle for reading.
    stats_file = args.dir + '/' + filename
    logging.debug('stats_file= ' + stats_file)

    bucketDictionary = {}
    # Get the stats for this zip files and place in thread local storage.
    stats_parse(bucketDictionary, file, stats_file, filename, progress_queue)

    #Output to splunk friendly log format
    output_logfile(stats_file, bucketDictionary)

    # Return the dictionary to the main process
    process_stats_queue.put(bucketDictionary)


def main():
    # Parse the arguments given.
    args = argumentParsing()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    logging.debug(args)

    if args.version:
        print("Version:" + str(globals.versionnumber))
        exit(0)

    # Find the path for the logparser package
    relativepath = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    matchObj= re.match(r'(.*)logparser.py$', sys.argv[0], re.I)
    if matchObj and matchObj.group(1) != '':
        relativepath = matchObj.group(1)
    logging.debug('relativepath = ' + relativepath)


    # Find all the files to load
    fileList = []
    for (dirpath, dirnames, filenames) in walk(args.dir):
        fileList.extend(filenames)
        break

    # process entry point map
    process_entry_functions = {
        'ns_server.stats':load_collectinfo
    }

    globals.loading_file = True

    # Load the stats files using python's multiprocessing
    # One process per stat type per zipfile.
    for filename in fileList:
        root, ext = os.path.splitext(filename)
        if ext == '.gz':
            logging.debug(filename)

            # Create the process data structures
            # - progress_queue is for sending messages about how far through the data crunching we are
            # - process_return_queue is for returning the final dictionary
            # - cached_progress is for the webserver, as we may always have a new progress to report 
            #   we would report the last known progress.
            globals.processes[filename] = {}
            for k in process_entry_functions:
                progress_queue = multiprocessing.Queue(1)
                process_return_queue = multiprocessing.Queue(1)
                process = multiprocessing.Process(target=process_entry_functions[k],
                                args=(filename, args, progress_queue, process_return_queue))
                globals.processes[filename][k] = {
                    'process' : process,
                    'progress_queue' : progress_queue,
                    'return_queue' : process_return_queue,
                    'cached_progress' : {'progress_end_size':1, 'progress_so_far':0}
                }

            # Start the processes
            for k in globals.processes[filename]:
                globals.processes[filename][k]['process'].start()

    # For each file collect each sub-process return data
    for filename in globals.processes:
        for key in globals.processes[filename]:
            globals.processes[filename][key]['stats'] = globals.processes[filename][key]['return_queue'].get()
            globals.processes[filename][key]['process'].join()


    logging.debug('finished loading tar fles')
    globals.loading_file = False
    return 0

if __name__ == '__main__':
    sys.exit(main())

