# logparser

Currently I can:-

 * Read ep\_engine stat information from  file in `diag` tar.gz file
 * Translate into Splunk friendly log format

 
logparser requires either `pypy` or `python 2.7.x` to be installed. 
 
	
# How to Use

## Starting logparser

To run logparser, simply type:-

    bin/logparser
    
If pypy is installed, logparser will automatically use it, otherwise it will default to use the standard python intepreter.    

By default, the current working directory will be searched for tar.gz files.

Each of these can be changed with command line flags.

    Usage:

      Switches                   Default  Desc
      --------                   -------  ----
      -h, --help                 no-help  show this help message and exit
      -d, --dir                  .        Directory to search for collectinfo .zips
      -v, --debug                false    Enable debugging messages
      --version                  Prints out the version number of logparser
      -e, --erlang               false    Analyze erlang related stats

See logparser/node_events.py for the dictionary which drives which files and events are looked at and what keys they are added as.

