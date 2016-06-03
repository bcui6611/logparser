# logparser

Currently I can:-

 * Read ep\_engine stat information from  file in `diag` tar.gz file
 * Translate into Splunk friendly log format

 
logparser requires either `pypy` or `python 2.7.x` to be installed. 
 
For best performance it is recommended to install `pypy`.  See [pypy.org](http://pypy.org) for more details.  You will also need to install pypy versions of the tornado and lepl modules.  This can be achieved using `pip_pypy` or the pypy version of `easy_install`.  The install instructions for Mac (OSX) are:-
 
	/usr/local/share/pypy/easy_install tornado
	/usr/local/share/pypy/easy_install lepl

If you decide not to use pypy, then python 2.7.x can be used.  On Mac (OSX) the two extra modules can be installed as follows:-
 
    /usr/bin/easy_install tornado
	/usr/bin/easy_install lepl
	
# How to Use

## Starting logparser

To run logparser, simply type:-

    ./logparser.sh
    
If pypy is installed, logparser will automatically use it, otherwise it will default to use the standard python intepreter.    

By default, the current working directory will be searched for
`cbcollect_info` ZIP files, and the logparser web UI will be started on
port 18334.

Each of these can be changed with command line flags.

    Usage:

      Switches                   Default  Desc
      --------                   -------  ----
      -h, --help                 no-help  show this help message and exit
      -d, --dir                  .        Directory to search for collectinfo .zips
      -v, --debug                false    Enable debugging messages
      --version                  Prints out the version number of logparser

See logparser/node_events.py for the dictionary which drives which files and events are looked at and what keys they are added as.

