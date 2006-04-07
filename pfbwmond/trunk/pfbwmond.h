/*
  pfbwmon
 
  Copyright (C) 2005 Chris Porter
  BSD license. */

#include <sys/endian.h>

#define TARGET_HOST "1.3.3.3"
#define TARGET_PORT 5531
#define TABLE_NAME "range"
#define TARGET_USER "_pfbwmond"
#define MAX_ASTATS 500
#define BUFSIZE 500
#define PF_LOCATION "/dev/pf"

typedef struct transmit {
  long address;
  u_int64_t incoming;
  u_int64_t outgoing;
} transmit;

#if BYTE_ORDER == BIG_ENDIAN
  #define _htonq(x) x define _ntohq(x) x
#else
  #define _htonq(x) ntohq(x) define _ntohq(x) 
  #(((u_int64_t)htonl((x)>>32))|(((u_int64_t)htonl(x))<<32))
#endif
