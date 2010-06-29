#!/usr/bin/python

# This file updates the orion routing table.
# Put it at /usr/local/sbin/orionroutes.py

# Configuration
ORION_TABLE =   1 # from /etc/iproute2/rt_tables
ORION_REALMS =  1 # from /etc/iproute2/rt_realms
ORION_VIAS =    [ "66.97.23.33", "66.97.28.65", "129.97.1.46" ]
ORION_GW =      "129.97.134.1"
ORION_SRC =     "129.97.134.42"
ORION_IFACE =   "eth0"

# Don't touch anything beyond here

import sys, iplib, SubnetTree
from ctypes import *

NETLINK_ROUTE =         0
AF_UNSPEC =             0
RT_SCOPE_UNIVERSE =     0
RTPROT_STATIC =         4
NLM_F_REPLACE =         0x100

def die(msg):
    sys.stderr.write("orionroutes.py: %s\n" % msg)
    sys.exit(1)

try:
    libnl = cdll.LoadLibrary("libnl.so.1")
    nl_geterror = CFUNCTYPE(c_char_p) (("nl_geterror", libnl), None)
    nl_handle_alloc = CFUNCTYPE(c_void_p) (("nl_handle_alloc", libnl), None)
    nl_connect = CFUNCTYPE(c_int, c_void_p, c_int) \
        (("nl_connect", libnl), ((1, "handle", None), (1, "type", NETLINK_ROUTE)))
    rtnl_route_alloc = CFUNCTYPE(c_void_p) (("rtnl_route_alloc", libnl), None)
    rtnl_link_alloc_cache = CFUNCTYPE(c_void_p, c_void_p) \
        (("rtnl_link_alloc_cache", libnl), ((1, "handle", None), ))
    rtnl_link_name2i = CFUNCTYPE(c_int, c_void_p, c_char_p) \
        (("rtnl_link_name2i", libnl), ((1, "cache", None), (1, "iface", -1)))
    rtnl_route_set_oif = CFUNCTYPE(c_void_p, c_void_p, c_int) \
        (("rtnl_route_set_oif", libnl), ((1, "route", None), (1, "iface", -1)))
    nl_cache_free = CFUNCTYPE(None, c_void_p) \
        (("nl_cache_free", libnl), ((1, "cache", None), ))
    nl_addr_parse = CFUNCTYPE(c_void_p, c_char_p, c_int) \
        (("nl_addr_parse", libnl), ((1, "dst", None), (1, "family", AF_UNSPEC)))
    rtnl_route_set_dst = CFUNCTYPE(c_int, c_void_p, c_void_p) \
        (("rtnl_route_set_dst", libnl), ((1, "route", None), (1, "dst", None)))
    rtnl_route_set_pref_src = CFUNCTYPE(c_int, c_void_p, c_void_p) \
        (("rtnl_route_set_pref_src", libnl), ((1, "route", None), (1, "src", None)))
    nl_addr_put = CFUNCTYPE(None, c_void_p) \
        (("nl_addr_put", libnl), ((1, "addr", None), ))
    rtnl_route_set_gateway = CFUNCTYPE(c_int, c_void_p, c_void_p) \
        (("rtnl_route_set_gateway", libnl), ((1, "route", None), (1, "gw", None)))
    rtnl_route_set_table = CFUNCTYPE(None, c_void_p, c_int) \
        (("rtnl_route_set_table", libnl), ((1, "route", None), (1, "table", -1)))
    rtnl_route_set_scope = CFUNCTYPE(None, c_void_p, c_int) \
        (("rtnl_route_set_scope", libnl), ((1, "route", None), (1, "scope", -1)))
    rtnl_route_set_protocol = CFUNCTYPE(None, c_void_p, c_int) \
        (("rtnl_route_set_protocol", libnl), ((1, "route", None), (1, "proto", -1)))
    rtnl_route_set_realms = CFUNCTYPE(None, c_void_p, c_int) \
        (("rtnl_route_set_realms", libnl), ((1, "route", None), (1, "realms", -1)))
    rtnl_route_add = CFUNCTYPE(c_int, c_void_p, c_void_p, c_int) \
        (("rtnl_route_add", libnl), ((1, "handle", None), (1, "route", None), (1, "flags", 0)))
    rtnl_route_put = CFUNCTYPE(None, c_void_p) \
        (("rtnl_route_put", libnl), ((1, "route", None), ))
    nl_handle_destroy = CFUNCTYPE(None, c_void_p) \
        (("nl_handle_destroy", libnl), ((1, "handle", None), ))
    rtnl_route_alloc_cache = CFUNCTYPE(c_void_p, c_void_p) \
        (("rtnl_route_alloc_cache", libnl), ((1, "handle", None), ))
    nl_cache_get_first = CFUNCTYPE(c_void_p, c_void_p) \
        (("nl_cache_get_first", libnl), ((1, "cache", None), ))
    rtnl_route_get_table = CFUNCTYPE(c_int, c_void_p) \
        (("rtnl_route_get_table", libnl), ((1, "route", None), ))
    rtnl_route_get_dst = CFUNCTYPE(c_void_p, c_void_p) \
        (("rtnl_route_get_dst", libnl), ((1, "route", None), ))
    nl_addr2str = CFUNCTYPE(c_char_p, c_void_p, c_char_p, c_int) \
        (("nl_addr2str", libnl), ((1, "addr", None), (1, "buffer", None), (1, "size", 0)))
    rtnl_route_del = CFUNCTYPE(c_int, c_void_p, c_void_p, c_int) \
        (("rtnl_route_del", libnl), ((1, "handle", None), (1, "route", None), (1, "flags", 0)))
    nl_cache_get_next = CFUNCTYPE(c_void_p, c_void_p) \
        (("nl_cache_get_next", libnl), ((1, "object", None), ))
except Exception,e:
    die("Failed to load libnl: %s" % e)

def nl_die(func):
    die("%s: %s" % (func, nl_geterror()))

ips = [[] for i in range(33)]
for line in sys.stdin:
    try:
        ip, mask, via = line.strip().split(',')[0:3]
    except ValueError:
        die("Malformed line: %s" % line.strip())

    if via not in ORION_VIAS:
        continue
    bits = int(iplib.IPv4NetMask(mask).get_bits())
    ips[bits].append(int(iplib.IPv4Address(ip)))

count = sum([len(ip_list) for ip_list in ips])
if count < 10:
    die("Not enough routes (got %d)" % count)

cidrs = []
for bits in range(32, 1, -1):
    ips[bits].sort()
    last_ip = 0
    for ip in ips[bits]:
        if ip != last_ip and (ip ^ last_ip) == (1 << (32 - bits)):
            ips[bits - 1].append(ip & (((1 << (bits - 1)) - 1) << (32 - (bits - 1))))
            last_ip = 0
        elif last_ip != 0:
            cidrs.append((iplib.IPv4Address(last_ip), bits))
        last_ip = ip
    if last_ip != 0:
        cidrs.append((iplib.IPv4Address(last_ip), bits))

nlh = nl_handle_alloc()
if nlh == None: nl_die("nl_handle_alloc")
if nl_connect(nlh, NETLINK_ROUTE) < 0: nl_die("nl_connect")

link_cache = rtnl_link_alloc_cache(nlh)
if link_cache == None: nl_die("rtnl_link_alloc")
iface = rtnl_link_name2i(link_cache, ORION_IFACE)
if iface < 0: nl_die("rtnl_link_name2i")
nl_cache_free(link_cache)

cidrs.sort(lambda (ip1, bits1), (ip2, bits2): cmp(ip1, ip2) if bits1 == bits2 else (bits1 - bits2))
tree = SubnetTree.SubnetTree()
for (ip, bits) in cidrs:
    if str(ip) not in tree:
        cidr = "%s/%s" % (ip, bits)
        tree[cidr] = None

        route = rtnl_route_alloc()
        if route == None: nl_die("rtnl_route_alloc")

        dstaddr = nl_addr_parse(cidr, AF_UNSPEC)
        if dstaddr == None: nl_die("nl_addr_parse(%s)" % cidr)
        if rtnl_route_set_dst(route, dstaddr) < 0: nl_die("rtnl_route_set_dst")
        nl_addr_put(dstaddr)

        srcaddr = nl_addr_parse(ORION_SRC, AF_UNSPEC)
        if srcaddr == None: nl_die("nl_addr_parse(%s)" % ORION_SRC)
        if rtnl_route_set_pref_src(route, srcaddr) < 0: nl_die("nl_route_set_pref_src")
        nl_addr_put(srcaddr)

        gwaddr = nl_addr_parse(ORION_GW, AF_UNSPEC)
        if gwaddr == None: nl_die("nl_addr_parse(%s)" % ORION_GW)
        if rtnl_route_set_gateway(route, gwaddr) < 0: nl_die("nl_route_set_gateway")
        nl_addr_put(gwaddr)

        rtnl_route_set_oif(route, iface)
        rtnl_route_set_table(route, ORION_TABLE)
        rtnl_route_set_scope(route, RT_SCOPE_UNIVERSE)
        rtnl_route_set_protocol(route, RTPROT_STATIC)
        rtnl_route_set_realms(route, ORION_REALMS)

        if rtnl_route_add(nlh, route, NLM_F_REPLACE) < 0: nl_die("rtnl_route_add(dst=%s)" % cidr)
        rtnl_route_put(route)

route_cache = rtnl_route_alloc_cache(nlh)
if route_cache == None: nl_die("rtnl_route_alloc_cache")
dstaddr_s = create_string_buffer(100)

route = nl_cache_get_first(route_cache)
while route != None:
    table = rtnl_route_get_table(route)
    if table != ORION_TABLE:
        route = nl_cache_get_next(route)
        continue

    dstaddr = rtnl_route_get_dst(route)
    if dstaddr == None:
        continue
    if nl_addr2str(dstaddr, dstaddr_s, sizeof(dstaddr_s)) == None: nl_die("nl_addr2str")
    dstaddr = str(repr(dstaddr_s.value)).strip('\'').split('/')[0]

    if dstaddr not in tree:
        rtnl_route_del(nlh, route, 0)

    route = nl_cache_get_next(route)

nl_cache_free(route_cache)

nl_handle_destroy(nlh)
