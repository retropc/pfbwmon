#!/usr/bin/env python
from socket import *
import sys
import struct
import os
import rrdtool

def daemonise():
  pid = os.fork()
  if pid:
    sys.exit(0)

  os.setsid()
  os.umask(0)
  os.close(sys.stdin.fileno())
  os.close(sys.stdout.fileno())
  os.close(sys.stderr.fileno())
  return pid

def dropprivs(user):
  import pwd
  if os.getuid() != 0:
    return

  pw = pwd.getpwnam(user)
  if not pw:
    sys.exit(1)

  os.chroot(pw[5]);
  os.chdir('/')

  os.setgroups([pw[3]])
  os.setgid(pw[3])
  os.setegid(pw[3])
  os.setuid(pw[2])
  os.seteuid(pw[2])

if len(sys.argv) == 2:
  configname = sys.argv[1]
else:
  configname = 'pfbwmon.conf'

try:
 config = eval(open(configname).read())
except IOError:
  print("Unable to open %s!" % configname)
  sys.exit(1)

if config.has_key('user'):
  dropprivs(config['user'])

buf = config['buf']
addr = config['addr']
fromaddr = config['fromaddr']
hosts = config['hosts']
rrdfile = config['rrdfile']

choice = 2000

if not os.path.exists(rrdfile):
  output = 'rrdtool.create(rrdfile, "--start", "N", "--step", "5", '
  for i in range(0, len(hosts)):
    output += "'DS:%sin:COUNTER:10:U:U', 'DS:%sout:COUNTER:10:U:U', " % (hosts[i][0], hosts[i][0])
  output += '"RRA:AVERAGE:0.5:1:1000", "RRA:AVERAGE:0.5:15:1250", "RRA:AVERAGE:0.5:100:1500", "RRA:AVERAGE:0.5:400:2000", "RRA:AVERAGE:0.5:6000:3000", "RRA:AVERAGE:0.5:60000:5000")'
  eval(output)

mappings = {}

for i in range(0, len(hosts)):
  ips = hosts[i][1]
  for j in range(0, len(ips)):
    mappings[ips[j]] = i

uso = socket(AF_INET, SOCK_DGRAM)
uso.bind(addr)

daemonise()

blah = -1
while 1:
  data, addr = uso.recvfrom(8192)
  if data and addr[0] == fromaddr:
    items = ord(data[0])

    data = data[1:]
    
    hash = []
    keys = mappings.keys()
    max = 0
    for key in keys:
      if mappings[key] > max:
        max = mappings[key]

    for i in range(0, max + 1):
      hash.insert(0, (0, 0))

    for i in range(0, items):
      ourdata = data[i * 20:i * 20 + 20]
      iin = struct.unpack("!Q", ourdata[4:12])[0]
      iout = struct.unpack("!Q", ourdata[12:20])[0]
      ip = inet_ntoa(ourdata[:4])
      if mappings.has_key(ip):
        pos = mappings[ip]
        hash[pos] = (hash[pos][0] + iin, hash[pos][1] + iout)

    output = "N:"
    while len(hash) > 0:
      item = hash.pop(0)
      output += "%d:%d:" % (item[0], item[1])
    rrdtool.update(rrdfile, output[:-1])

