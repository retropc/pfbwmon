/*
  pfbwmon
 
  Copyright (C) 2005 Chris Porter
  BSD license.
*/

#include <sys/types.h>
#include <sys/ioctl.h>
#include <sys/socket.h>
#include <netdb.h>
#include <unistd.h>

#include <net/if.h>
#include <net/pfvar.h>

#include <stdio.h>
#include <stdlib.h>
#include <sys/fcntl.h>
#include <assert.h>
#include <pwd.h>

#include "pfbwmond.h"

int handle;

int transmitdata(int sock, transmit *data, int size, struct sockaddr_in *addr) {
  char buffer[BUFSIZE];
  unsigned char csize = size;
  int i;
  assert((sizeof(buffer) - 1) >= sizeof(*data) * size);
  assert(csize == size);

  buffer[0] = csize;

  for(i=0;i<size;i++)
    memcpy(buffer + 1 + i * sizeof(*data), &data[i], sizeof(*data));

  return sendto(sock, buffer, size * sizeof(*data) + 1, 0, (struct sockaddr *)addr, sizeof(*addr));
}

int gettables(struct pfr_table *table, int size) {
  struct pfioc_table io;

  memset(&io, 0, sizeof(io));
  io.pfrio_buffer = table;
  io.pfrio_esize = sizeof(struct pfr_table);
  io.pfrio_size = size;
  if(ioctl(handle, DIOCRGETTABLES, &io))
    return -1;

  return io.pfrio_size;
}

int getastats(struct pfr_table *table, struct pfr_astats *astats, int size) {
  struct pfioc_table io;

  memset(&io, 0, sizeof(io));

  io.pfrio_buffer = astats;
  io.pfrio_esize = sizeof(struct pfr_astats);
  io.pfrio_size = size;
  io.pfrio_table = *table;

  if(ioctl(handle, DIOCRGETASTATS, &io))
    return -1;

  return io.pfrio_size;
}

int openhandle(void) {
  return open(PF_LOCATION, O_RDWR);
}

void FATAL(char *message) {
  printf("%s\n", message);
  exit(1);
}

void FATALE(char *message) {
  perror(message);
  exit(1);
}

void dropprivs(void) {
  struct passwd *pw;
  if(!(pw = getpwnam(TARGET_USER)))
    FATALE("getpwnam");

  if(chroot(pw->pw_dir) < 0)
    FATALE("chroot");

  if(chdir("/") < 0)
    FATALE("chdir");

  if(setgroups(1, &pw->pw_gid))
    FATALE("setgroups");

  if(setgid(pw->pw_gid))
    FATALE("setgid");

  if(setegid(pw->pw_gid))
    FATALE("setegid");

  if(setuid(pw->pw_uid))
    FATALE("setuid");

  if(seteuid(pw->pw_uid))
    FATALE("seteuid");
}

void daemonise(int dn) {
  pid_t pid, sid;
  int fd;

  pid = fork();
  if(pid < 0)
    FATALE("fork");

  if(pid > 0)
    exit(0);

  sid = setsid();
  if(sid < 0)
    _exit(1);

  if((dup2(dn, STDIN_FILENO) < 0) || (dup2(dn, STDOUT_FILENO) < 0) || (dup2(dn, STDERR_FILENO) < 0))
    _exit(1);
}

int main(void) {
  struct pfioc_table io;
  struct pfr_table table;
  struct pfr_astats stats[MAX_ASTATS];
  struct hostent *host;
  transmit netdata[MAX_ASTATS];
  int statcount;
  int sock, dn;
  struct sockaddr_in addr;

  dn = open("/dev/null", O_RDWR);
  if(dn == -1)
    FATALE("open devnull");

  handle = openhandle();
  if(handle == -1)
    FATALE("opening pf");

  dropprivs();
  daemonise(dn);

  memset(&table, 0, sizeof(table));
  if(strlcpy(table.pfrt_name, TABLE_NAME, sizeof(table.pfrt_name)) >= sizeof(table.pfrt_name))
    FATAL("Table name too long!");

  sock = socket(AF_INET, SOCK_DGRAM, 0);
  if(!sock)
    FATALE("socket");

  host = gethostbyname(TARGET_HOST);
  if(!host)
    FATALE("gethostbyname");

  memset(&addr, 0, sizeof(addr));
  memcpy(&addr.sin_addr.s_addr, host->h_addr, host->h_length);

  addr.sin_family = AF_INET;
  addr.sin_port = htons(TARGET_PORT);

  /* fork */

  for(;;) {
    statcount = getastats(&table, stats, sizeof(stats) / sizeof(struct pfr_astats));
    if(statcount > 0) {
      int i;
      for(i=0;i<statcount;i++) {
        /* I KNOW this is shitty... */
        netdata[i].address = stats[i].pfras_a.pfra_ip4addr.s_addr;
        netdata[i].incoming = _htonq(stats[i].pfras_bytes[0][1]);
        netdata[i].outgoing = _htonq(stats[i].pfras_bytes[1][1]);   
      }
      transmitdata(sock, netdata, statcount, &addr);
    }
    sleep(5);
  }

  close(handle);
  return 0;
}
