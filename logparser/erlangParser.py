#!/usr/bin/env python2.7

from __future__ import print_function
import logging
import sys
import time
import pprint
try:
    from pyparsing import *
except ImportError:
    is_pypy = '__pypy__' in sys.builtin_module_names
    print("ERROR: erlangParser requires the 'pyparsing' module. Install using:\n")
    if is_pypy:
        print("    pip_pypy install pyparsing\n")
    else:
        print("    pip install pyparsing\n"
              "or\n"
              "    easy_install pyparsing\n", file=sys.stderr)
    exit(1)

TRUE = Keyword("true").setParseAction( replaceWith(True) )
FALSE = Keyword("false").setParseAction( replaceWith(False) )
NULL = Keyword("null").setParseAction( replaceWith(None) )

# Erlang config file definition:
erlangQuotedAtom = sglQuotedString.setParseAction( removeQuotes )
erlangRegExAtom = Regex(r'[a-z][a-z0-9_]+')
erlangAtom = ( erlangRegExAtom | erlangQuotedAtom )
erlangString = Regex(r'"(?:[^"\\]|(?:"")|(?:\\x[0-9a-fA-F]+)|(?:\\.))*"').setName("string enclosed in double quotes")

erlangBitString = Suppress('<<') + Optional(erlangString) + Suppress('>>')
erlangNumber = Regex(r'[-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?')
erlangPid = Regex("<\d+\.\d+\.\d+>")
erlangConfig = Forward()
erlangValue = Forward()
erlangList = Forward()

erlangElements = delimitedList( erlangValue )
erlangCSList = Suppress('[') + Optional(erlangElements) + Suppress(']')
erlangHeadTailList = Suppress('[') + erlangValue + Suppress('|') + erlangValue + Suppress(']')
erlangList <<= Group( erlangCSList | erlangHeadTailList )
erlangTuple = Group( Suppress('{') + Optional(erlangElements) + Suppress('}') )

erlangDictKey = erlangAtom | erlangBitString
erlangTaggedTuple = Suppress('{') + Group( erlangDictKey + Suppress(',') + erlangValue ) + Suppress('}')
erlangTaggedTupleList = delimitedList( erlangTaggedTuple )
erlangDict = Group( Suppress('[') + Dict( erlangTaggedTupleList ) + Suppress(']') )

erlangValue <<= ( erlangAtom | erlangNumber | erlangString |
                  erlangBitString | erlangPid | erlangTaggedTuple |
                  erlangTuple | erlangDict | erlangList )


erlangConfig << Dict( Suppress('[') + Optional(erlangElements) + Suppress(']') )

def convertNumbers(s,l,toks):
    n = toks[0]
    try:
        return int(n)
    except ValueError, ve:
        return float(n)

erlangNumber.setParseAction( convertNumbers )
erlangString.setParseAction( removeQuotes )

def listToTuple ( l ):
    """Convert a list (and any sublists) to a tuple."""
    for index, val in enumerate(l):
        if isinstance(val, list):
            l[index] = tuple(val)
    return tuple(l)

def convertToDict( p ):
    """Converts a ParseResults 'dict' (as returned by asDict()) into a
    proper dictionary."""

    # Check for a ParseResult which is actually a list (i.e. all values are
    # empty)
    if not p.keys():
        out = []
        for item in p:
            if isinstance( item, ParseResults):
                out.append(convertToDict(item))
            else:
                out.append(item)
        return out
    else:
        out = {}
        for k in p.keys():
            v = p[k]
            if isinstance( k, ParseResults):
                k = listToTuple(k.asList())
            if isinstance( v, ParseResults):
                v = convertToDict(v)
            out[k] = v
        return out


def parseErlangConfig(str):
    """Given Erlang config data in the specified string, parse it."""
    try:
        config = erlangConfig.parseString(str)
        # Convert to plain dict (so it can be pickled when using
        # multiprocessing).
        config = convertToDict(config)
        return config
    except ParseException, err:
        #logging.error(err.line)
        #logging.error(" "*(err.column-1) + "^")
        #logging.error(err)
        #raise
        return []

def parseErlangValue(string):
    """Given Erlang value, parse and return as Python dict."""
    try:
        d = erlangValue.parseString(string)
        return convertToDict(d)
    except ParseException, err:
        #logging.error(err.line)
        #logging.error(" "*(err.column-1) + "^")
        #logging.error(err)
        #raise
        return []


if __name__ == "__main__":
    testdata0="""
[{'ns_1@127.0.0.1',
     [{last_heard,{1462,992075,377815}},
      {now,{1462,992075,360141}},
      {active_buckets,["default"]},
      {ready_buckets,["default"]},
      {status_latency,17580},
      {outgoing_replications_safeness_level,[{"default",green}]},
      {incoming_replications_conf_hashes,[{"default",[]}]},
      {local_tasks,[]},
      {memory,
          [{total,55200856},
           {processes,27323472},
           {processes_used,27301512},
           {system,27877384},
           {atom,586345},
           {atom_used,565523},
           {binary,2744168},
           {code,14453678},
           {ets,4118736}]},
      {system_memory_data,
          [{total_memory,14774349824},
           {free_memory,7056166912},
           {system_total_memory,14774349824}]},
      {node_storage_conf,
          [{db_path,
               "/Users/bincui/Library/Application Support/Couchbase/var/lib/couchdb"},
           {index_path,
               "/Users/bincui/Library/Application Support/Couchbase/var/lib/couchdb"}]},
      {statistics,
          [{wall_clock,{59046,1313}},
           {context_switches,{90156,0}},
           {garbage_collection,{20217,144536700,0}},
           {io,{{input,14769272},{output,6694804}}},
           {reductions,{78496167,114289}},
           {run_queue,0},
           {runtime,{4520,40}},
           {run_queues,{0,0,0,0,0,0,0,0}}]},
      {system_stats,
          [{cpu_utilization_rate,13.375},
           {swap_total,0},
           {swap_used,0},
           {mem_total,17179869184},
           {mem_free,8862568448}]},
      {interesting_stats,
          [{cmd_get,0.0},
           {couch_docs_actual_disk_size,542775},
           {couch_docs_data_size,0},
           {couch_views_actual_disk_size,0},
           {couch_views_data_size,0},
           {curr_items,0},
           {curr_items_tot,0},
           {ep_bg_fetched,0.0},
           {get_hits,0.0},
           {mem_used,2810784},
           {ops,0.0},
           {vb_replica_curr_items,0}]},
      {per_bucket_interesting_stats,
          [{"default",
            [{cmd_get,0.0},
             {couch_docs_actual_disk_size,542775},
             {couch_docs_data_size,0},
             {couch_views_actual_disk_size,0},
             {couch_views_data_size,0},
             {curr_items,0},
             {curr_items_tot,0},
             {ep_bg_fetched,0.0},
             {get_hits,0.0},
             {mem_used,2810784},
             {ops,0.0},
             {vb_replica_curr_items,0}]}]},
      {processes_stats,
          [{<<"proc/(main)beam.smp/cpu_utilization">>,0},
           {<<"proc/(main)beam.smp/major_faults">>,0},
           {<<"proc/(main)beam.smp/major_faults_raw">>,0},
           {<<"proc/(main)beam.smp/mem_resident">>,0},
           {<<"proc/(main)beam.smp/mem_share">>,0},
           {<<"proc/(main)beam.smp/mem_size">>,28262273935303020},
           {<<"proc/(main)beam.smp/minor_faults">>,0},
           {<<"proc/(main)beam.smp/minor_faults_raw">>,0},
           {<<"proc/(main)beam.smp/page_faults">>,0},
           {<<"proc/(main)beam.smp/page_faults_raw">>,0},
           {<<"proc/beam.smp/cpu_utilization">>,0},
           {<<"proc/beam.smp/major_faults">>,0},
           {<<"proc/beam.smp/major_faults_raw">>,0},
           {<<"proc/beam.smp/mem_resident">>,0},
           {<<"proc/beam.smp/mem_share">>,0},
           {<<"proc/beam.smp/mem_size">>,28262273935303020},
           {<<"proc/beam.smp/minor_faults">>,0},
           {<<"proc/beam.smp/minor_faults_raw">>,0},
           {<<"proc/beam.smp/page_faults">>,0},
           {<<"proc/beam.smp/page_faults_raw">>,0},
           {<<"proc/memcached/cpu_utilization">>,0},
           {<<"proc/memcached/major_faults">>,0},
           {<<"proc/memcached/major_faults_raw">>,0},
           {<<"proc/memcached/mem_resident">>,0},
           {<<"proc/memcached/mem_share">>,0},
           {<<"proc/memcached/mem_size">>,28262273935303020},
           {<<"proc/memcached/minor_faults">>,0},
           {<<"proc/memcached/minor_faults_raw">>,0},
           {<<"proc/memcached/page_faults">>,0},
           {<<"proc/memcached/page_faults_raw">>,0}]},
      {cluster_compatibility_version,196608},
      {version,
          [{lhttpc,"1.3.0"},
           {os_mon,"2.2.14"},
           {public_key,"0.21"},
           {asn1,"2.0.4"},
           {couch,"2.1.1r-464-gc3943b0"},
           {kernel,"2.16.4"},
           {syntax_tools,"1.6.12"},
           {xmerl,"1.3.5"},
           {ale,"3.1.5-1859-rel-enterprise"},
           {couch_set_view,"2.1.1r-464-gc3943b0"},
           {compiler,"4.9.4"},
           {inets,"5.9.7"},
           {mapreduce,"1.0.0"},
           {couch_index_merger,"2.1.1r-464-gc3943b0"},
           {ns_server,"3.1.5-1859-rel-enterprise"},
           {oauth,"7d85d3ef"},
           {crypto,"3.2"},
           {ssl,"5.3.2"},
           {sasl,"2.3.4"},
           {couch_view_parser,"1.0.0"},
           {mochiweb,"2.4.2"},
           {stdlib,"1.19.4"}]},
      {supported_compat_version,[3,0]},
      {advertised_version,[3,1,1]},
      {system_arch,"x86_64-apple-darwin10.8.0"},
      {wall_clock,59},
      {memory_data,{14826999808,7473250304,{<0.7.0>,1203224}}},
      {disk_data,[{"/",243924992,38}]}]}]
"""
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            testdata = f.read()
            for i in range(100):
                result = parseErlangValue(testdata)
            #pprint.pprint( result )

    else:
        t = time.clock() 
        results = parseErlangConfig(testdata)
        process_time = time.clock() - t
        print("Took {0}".format(process_time))
        pprint.pprint( results['ns_1@127.0.0.1'] )
        print

