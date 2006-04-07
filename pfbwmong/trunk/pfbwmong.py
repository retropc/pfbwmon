#!/usr/bin/env python
import sys
import os
import rrdtool

if len(sys.argv) == 2:
  configname = sys.argv[1]
else:
  configname = 'pfbwmon.conf'

try:
 config = eval(open(configname).read())
except IOError:
  print("Unable to open %s!" % configname)
  sys.exit(1)

hosts = config['hosts']
path = config['path']
graphs = config['graphs']
rrdfile = config['rrdfile']

if not os.path.exists(rrdfile):
  import pwd
  pw = pwd.getpwnam(config['user'])
  if pw:
    rrdfile = pw[5] + "/" + rrdfile 
    if not os.path.exists(rrdfile):
      sys.exit(1)
  else:
    sys.exit(1)

mappings = {}

defs2 = []
stacks2a = []
stacks2b = []

first = 0

for i in range(0, len(hosts)):
  if hosts[i][3] == 0:
    defs2.append('DEF:%sin=%s:%sin:AVERAGE' % (hosts[i][0], rrdfile, hosts[i][0]))
    defs2.append('DEF:%sout_n=%s:%sout:AVERAGE' % (hosts[i][0], rrdfile, hosts[i][0]))
    defs2.append('CDEF:%sout=%sout_n,-1,*' % (hosts[i][0], hosts[i][0]))

    if not first:
      first = 1
      gtype = "AREA"
    else: 
      gtype = "STACK"

    stacks2a.append('%s:%sin%s:%s' % (gtype, hosts[i][0], hosts[i][2], hosts[i][0]))
    stacks2b.append('%s:%sout%s' % (gtype, hosts[i][0], hosts[i][2]))


dataline = 'CDEF:totalin='
dataend = ''
for i in range(0, len(hosts)):
  if hosts[i][3] == 0:
    dataline += "%sin," % hosts[i][0]
    dataend += '+,'

defs2.append(dataline + dataend[:-3])

dataline = 'CDEF:totalout_n='
for i in range(0, len(hosts)):
  if hosts[i][3] == 0:
    dataline += "%sout_n," % hosts[i][0]

defs2.append(dataline + dataend[:-3])
#defs2.append('CDEF:totalout=totalout_n,-1,*')

stacks2b.append('COMMENT:\j')
stacks2b.append('COMMENT:Current')
stacks2b.append('COMMENT:Average              \j')
stacks2b.append('GPRINT:totalin:LAST:Incoming\: %6.2lf %Sbps')
stacks2b.append('GPRINT:totalin:AVERAGE:Incoming\: %6.2lf %Sbps\j')
stacks2b.append('GPRINT:totalout_n:LAST:Outgoing\: %6.2lf %Sbps')
stacks2b.append('GPRINT:totalout_n:AVERAGE:Outgoing\: %6.2lf %Sbps\j')

args = ["-a", "PNG", "-h", "%d" % config['height'], "--width", "%d" % config['width'], "-v", "bytes per second"] + defs2 + stacks2a + stacks2b + ['HRULE:0#000000']

graphoutput = []

for i in range(0, len(graphs)):
  filename = path + graphs[i][0]
  item = [filename, "-s", "-%d" % graphs[i][1]] + args
  graphoutput.append('rrdtool.graph(%s)' % (repr(item)[1:-1]))

for i in range(0, len(graphoutput)):
  eval(graphoutput[i])

