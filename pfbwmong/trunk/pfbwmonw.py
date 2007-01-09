#!/usr/bin/env python
from socket import *
import sys
import struct
import os
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

permitted = []

class handler(BaseHTTPRequestHandler):
  def do_GET(self):
    page = self.path
    try:

      if page and (page[0] == '/'):
        page = page[1:]

      if page == '':
        page = 'index.html'

      l = permitted[page]
      f = open(page)

      self.send_response(200)
      self.send_header('Content-type', l)
      self.send_header("Cache-Control", "no-cache, must-revalidate")
      self.send_header("Expires", "Mon, 26 Jul 1997 05:00:00 GMT")
      self.end_headers()
      self.wfile.write(f.read())
      f.close()

    except:
      self.ourerror(404, "File not found")
    
    return

  def do_POST(self):
    self.ourerror(403)

  def ourerror(self, code, text):
    self.send_response(code)
    self.send_header('Content-type', 'text/html')
    self.end_headers()
    self.wfile.write('<html><head><title>Error %d</title></head><body><h1>Error %d</h1><p>%s</p></body></html>' % (code, code, text))
    return

def daemonise():
  pid = os.fork()
  if pid:
    sys.exit(0)

  sys.stdin.close()
  sys.stdout.close()
  sys.stderr.close()

  sys.stdin = stdin
  sys.stdout = stdout
  sys.stderr = stderr

  os.setsid()
  os.umask(0)

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

stdin = open('/dev/null')      
stdout = open('/dev/null', 'w')
stderr = open('/dev/null', 'w')

dropprivs(config['wwwuser'])

permitted = config['wwwpages']

port = 5580

if config.has_key('wwwport'):
  port = int(config['wwwport'])

server = HTTPServer(('', port), handler)

daemonise()

server.serve_forever()
