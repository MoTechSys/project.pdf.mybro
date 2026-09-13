#!/usr/bin/env python3
"""Build a reproducible campus design and IOS configuration set (not simulator evidence)."""
from __future__ import annotations
import csv
import ipaddress as ip
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDINGS = {
 'A': ('Computer and IT', 10, [(10,'ADMIN',24,'admin'),(20,'FACULTY',48,'faculty'),(30,'CYBER_STUDENTS',120,'student'),(31,'NETWORK_STUDENTS',100,'student'),(32,'SOFTWARE_STUDENTS',140,'student'),(40,'LABS',100,'student'),(60,'GUEST',80,'guest'),(70,'VOICE',60,'voice'),(80,'SECURITY',16,'security'),(99,'MANAGEMENT',16,'management')]),
 'B': ('Engineering', 20, [(10,'ADMIN',20,'admin'),(20,'FACULTY',40,'faculty'),(30,'CIVIL_STUDENTS',140,'student'),(31,'ELECTRICAL_STUDENTS',160,'student'),(40,'LABS',80,'student'),(60,'GUEST',60,'guest'),(70,'VOICE',48,'voice'),(80,'SECURITY',16,'security'),(99,'MANAGEMENT',16,'management')]),
 'C': ('Science', 30, [(10,'ADMIN',20,'admin'),(20,'FACULTY',36,'faculty'),(30,'PHYSICS_STUDENTS',110,'student'),(31,'CHEMISTRY_STUDENTS',130,'student'),(40,'LABS',80,'student'),(60,'GUEST',60,'guest'),(70,'VOICE',44,'voice'),(80,'SECURITY',16,'security'),(99,'MANAGEMENT',16,'management')]),
 'D': ('Business and Economics', 40, [(10,'ADMIN',24,'admin'),(20,'FACULTY',40,'faculty'),(30,'BUSINESS_STUDENTS',120,'student'),(31,'ACCOUNTING_STUDENTS',100,'student'),(32,'ECONOMICS_STUDENTS',80,'student'),(60,'GUEST',60,'guest'),(70,'VOICE',48,'voice'),(80,'SECURITY',12,'security'),(99,'MANAGEMENT',16,'management')]),
 'E': ('Administration and Data Center', 50, [(10,'UNIVERSITY_ADMIN',40,'admin'),(11,'STUDENT_AFFAIRS',60,'admin'),(12,'HR',28,'hr'),(13,'FINANCE',28,'finance'),(50,'SERVERS',24,'server'),(60,'GUEST',40,'guest'),(70,'VOICE',70,'voice'),(80,'SECURITY',20,'security'),(99,'MANAGEMENT',24,'management')]),
}

def write(path, text):
 p = ROOT / path
 p.parent.mkdir(parents=True, exist_ok=True)
 p.write_text(text, encoding='utf-8')

def csvfile(path, rows):
 p = ROOT / path
 p.parent.mkdir(parents=True, exist_ok=True)
 with p.open('w', newline='', encoding='utf-8-sig') as f:
  writer = csv.DictWriter(f, fieldnames=list(rows[0]))
  writer.writeheader(); writer.writerows(rows)

subnets = []
for building, (title, second, entries) in BUILDINGS.items():
 cursor = int(ip.ip_address(f'10.{second}.0.0'))
 sized = [(32-math.ceil(math.log2(math.ceil(count*1.25)+15+2)), vid, name, count, role) for vid,name,count,role in entries]
 for prefix, vid, name, count, role in sorted(sized):
  n = ip.ip_network((cursor, prefix)); cursor += n.num_addresses
  addr = lambda offset: str(n.network_address+offset)
  subnets.append(dict(building=building,vlan=vid,name=name,role=role,assumed_endpoints=count,growth_endpoints=math.ceil(count*1.25),reserved_hosts=15,network=str(n),mask=str(n.netmask),wildcard=str(n.hostmask),first_host=addr(1),last_host=str(n.broadcast_address-1),broadcast=str(n.broadcast_address),usable=n.num_addresses-2,endpoint_capacity=n.num_addresses-17,vip=addr(1),dist1=addr(2),dist2=addr(3),dhcp_start=addr(16) if role not in ('management','server','security') else '',dhcp_end=str(n.broadcast_address-1) if role not in ('management','server','security') else ''))
subnets.sort(key=lambda x:(x['building'],x['vlan']))
lookup = {(s['building'],s['vlan']):s for s in subnets}
def host(s, offset): return str(ip.ip_network(s['network']).network_address+offset)
server = lookup['E',50]
DHCP = host(server,10); DNS = host(server,11); WEB = host(server,12)
IT = host(lookup['E',99],10)
PUBLIC = '203.0.113.10'

nodes = []
links = []
def node(name,model,layer,building='',rid='',mgmt=''):
 nodes.append(dict(name=name,model=model,layer=layer,building=building,router_id=rid,management_ip=mgmt))
def link(a,ap,b,bp,network='',aip='',bip='',kind='routed'):
 links.append(dict(a=a,a_port=ap,b=b,b_port=bp,kind=kind,network=network,a_ip=aip,b_ip=bip))
node('CORE-1','3650-24PS','Core',rid='10.255.255.1',mgmt=host(lookup['E',99],4))
node('CORE-2','3650-24PS','Core',rid='10.255.255.2',mgmt=host(lookup['E',99],5))
transit = iter(ip.ip_network('10.0.0.0/24').subnets(new_prefix=30))
def routed(a,ap,b,bp):
 n=next(transit); h=list(n.hosts()); link(a,ap,b,bp,str(n),str(h[0]),str(h[1]))
routed('CORE-1','GigabitEthernet1/0/11','CORE-2','GigabitEthernet1/0/11')
for bi,b in enumerate(BUILDINGS):
 for d in (1,2):
  name=f'DIST-{b}{d}'
  node(name,'2911','Distribution',b,f'10.255.255.{11+bi*2+d-1}',lookup[b,99][f'dist{d}'])
  for c in (1,2): routed(f'CORE-{c}',f'GigabitEthernet1/0/{bi*2+d}',name,f'GigabitEthernet0/{c-1}')
 for a in (1,2):
  name=f'ACC-{b}{a}'; node(name,'2960-24TT','Access',b,mgmt=host(lookup[b,99],10+a))
  link(f'DIST-{b}{a}','GigabitEthernet0/2',name,'GigabitEthernet0/1',kind='trunk')
 link(f'ACC-{b}1','GigabitEthernet0/2',f'ACC-{b}2','GigabitEthernet0/2',kind='trunk')
node('EDGE','2911','Border',rid='10.255.255.30',mgmt=host(lookup['E',99],6))
routed('CORE-1','GigabitEthernet1/0/12','EDGE','GigabitEthernet0/0')
routed('CORE-2','GigabitEthernet1/0/12','EDGE','GigabitEthernet0/1')
node('ISP','2911','External')
link('EDGE','GigabitEthernet0/2','ISP','GigabitEthernet0/0','198.51.100.0/30','198.51.100.1','198.51.100.2')
node('DHCP-1','2911','Service','E',mgmt=DHCP)
link('DHCP-1','GigabitEthernet0/0','ACC-E2','FastEthernet0/1',kind='access:50')
for c in (1,2): link(f'CORE-{c}','GigabitEthernet1/0/24','ACC-E2',f'FastEthernet0/{19+c}',kind='access:99')
# EDGE management uses Loopback99 in a separate /32; its three physical ports are all required.
next(n for n in nodes if n['name']=='EDGE')['management_ip']='10.255.254.30'

endpoints = []
for b in BUILDINGS:
 for i,s in enumerate([x for x in subnets if x['building']==b and x['role'] not in ('management','server')],1):
  name=f'{b}-{s["name"]}-PC'
  endpoints.append(dict(name=name,building=b,vlan=s['vlan'],switch=f'ACC-{b}1',port=f'FastEthernet0/{i}',ip='DHCP' if s['dhcp_start'] else host(s,16),mask=s['mask'],gateway=s['vip'],dns=DNS,role=s['role']))
  link(name,'FastEthernet0',f'ACC-{b}1',f'FastEthernet0/{i}',kind=f'access:{s["vlan"]}')
for name,vid,port,offset,role in [('DNS-SERVER',50,2,11,'dns'),('EDU-WEB',50,3,12,'web'),('IT-ADMIN',99,4,10,'management'),('HR-TEST',12,5,16,'hr'),('FINANCE-TEST',13,6,16,'finance')]:
 s=lookup['E',vid]
 # HR/Finance extra hosts use DHCP to avoid overlapping manually assigned dynamic addresses.
 address='DHCP' if role in ('hr','finance') else host(s,offset)
 endpoints.append(dict(name=name,building='E',vlan=vid,switch='ACC-E2',port=f'FastEthernet0/{port}',ip=address,mask=s['mask'],gateway=s['vip'],dns=DNS,role=role))
 link(name,'FastEthernet0','ACC-E2',f'FastEthernet0/{port}',kind=f'access:{vid}')
endpoints.append(dict(name='PUBLIC-WEB',building='ISP',vlan=0,switch='ISP',port='GigabitEthernet0/1',ip=PUBLIC,mask='255.255.255.0',gateway='203.0.113.1',dns=DNS,role='external'))
link('ISP','GigabitEthernet0/1','PUBLIC-WEB','FastEthernet0','203.0.113.0/24','203.0.113.1',PUBLIC,kind='external')


def common(name, routed_device=True):
 return ['enable','configure terminal',f'hostname {name}','no ip domain-lookup','ip domain-name campus.example','enable secret LabOnly26Enable9','username netadmin privilege 15 secret LabOnly26Admin9','service password-encryption','banner motd #AUTHORIZED CAMPUS IT ACCESS ONLY. ACTIVITY MAY BE MONITORED.#','no ip http server','no ip http secure-server',*(['ip routing'] if routed_device and name.startswith('CORE') else []),'ip access-list standard VTY-IT',f' permit host {IT}',' deny any','exit','line console 0',' login local',' exec-timeout 10 0',' logging synchronous','exit','line vty 0 4',' login local',' transport input ssh',' access-class VTY-IT in',' exec-timeout 5 0','exit',*(['line vty 5 15',' login local',' transport input ssh',' access-class VTY-IT in',' exec-timeout 5 0','exit'] if name.startswith(('CORE','ACC')) else []),'crypto key generate rsa general-keys modulus 2048','ip ssh version 2']

def end(lines): return '\n'.join(lines+['end','write memory',''])

def interfaces_for(name):
 for l in links:
  if l['kind']=='routed' and name in (l['a'],l['b']):
   side='a' if name==l['a'] else 'b'; other='b' if side=='a' else 'a'
   yield l,side,other

def routing(name):
 n=next(x for x in nodes if x['name']==name)
 lines=['interface Loopback0',f' ip address {n["router_id"]} 255.255.255.255','exit']
 active=[]
 for l,side,other in interfaces_for(name):
  if 'ISP' in (l['a'],l['b']): continue
  interface=l[f'{side}_port']; active.append(interface)
  lines += [f'interface {interface}',f' description TO_{l[other]}_{l[f"{other}_port"]}',*([' no switchport'] if name.startswith('CORE') else []),f' ip address {l[f"{side}_ip"]} 255.255.255.252',' ip ospf network point-to-point',' no shutdown','exit']
 lines += ['router ospf 1',f' router-id {n["router_id"]}',' passive-interface default']
 lines += [f' no passive-interface {p}' for p in active]
 for l,side,_ in interfaces_for(name):
  if 'ISP' not in (l['a'],l['b']): lines += [f' network {l[f"{side}_ip"]} 0.0.0.0 area 0']
 lines += [f' network {n["router_id"]} 0.0.0.0 area 0']
 if name.startswith('DIST'):
  lines += [f' network {s["dist1" if name.endswith("1") else "dist2"]} 0.0.0.0 area 0' for s in subnets if s['building']==n['building']]
 if name=='EDGE': lines += [' network 10.255.254.30 0.0.0.0 area 0',' default-information originate']
 return lines+['exit']

# Each ACL is mirrored on the HSRP peers. Matching source prefixes is anti-spoofing between VLANs.
acls = {}
def make_acl(s):
 n=ip.ip_network(s['network']); src=f'{n.network_address} {n.hostmask}'; role=s['role']
 rules=[]
 for peer in (s['dist1'],s['dist2']): rules.append(f'permit udp host {peer} eq 1985 host 224.0.0.2 eq 1985')
 rules += ['permit udp any eq 68 host 255.255.255.255 eq 67',f'permit udp {src} eq 68 host {DHCP} eq 67']
 # Only infrastructure servers may return traffic to the authorized IT workstation.
 # IOS established matches TCP flags, not a stateful connection table.
 if role=='server': rules += [f'permit tcp {src} host {IT} established',f'permit icmp {src} host {IT} echo-reply',f'permit udp host {DHCP} eq 67 any eq 67',f'permit udp host {DHCP} eq 67 any eq 68',f'permit udp host {DNS} eq 53 host {IT}']
 for mg in [x for x in subnets if x['role']=='management']:
  mn=ip.ip_network(mg['network']); rules.append(f'deny ip any {mn.network_address} {mn.hostmask}')
 # Deny routed infrastructure, including border management, before business-service permits.
 rules += ['deny ip any 10.0.0.0 0.0.0.255','deny ip any 10.255.254.0 0.0.1.255']
 # Real and virtual SVI addresses may forward traffic but are not user-accessible endpoints.
 for vlan in subnets:
  if vlan['role']!='management':
   rules += [f'deny ip any host {vlan[k]}' for k in ('vip','dist1','dist2')]
 rules += [f'permit udp {src} host {DNS} eq 53',f'permit tcp {src} host {DNS} eq 53']
 if role in ('student','voice','security'):
  rules += [f'permit tcp {src} host {WEB} eq 80',f'permit tcp {src} host {WEB} eq 443']
 elif role=='faculty':
  sn=ip.ip_network(server['network']); rules += [f'permit ip {src} {sn.network_address} {sn.hostmask}']
 elif role in ('admin','hr','finance','server'):
  rules += [f'permit ip {src} 10.0.0.0 0.255.255.255']
 rules += ['deny ip any 10.0.0.0 0.255.255.255','deny ip any 172.16.0.0 0.15.255.255','deny ip any 192.168.0.0 0.0.255.255']
 if role not in ('voice','security'): rules.append(f'permit ip {src} any')
 rules.append('deny ip any any')
 return rules
for s in subnets:
 if s['role']!='management': acls[f'{s["building"]}-V{s["vlan"]}-IN']=make_acl(s)

for c in (1,2):
 name=f'CORE-{c}'; lines=common(name)+routing(name)
 lines += ['interface GigabitEthernet1/0/24',' description DEDICATED_MANAGEMENT_TO_ACC_E2',' no cdp enable',' no switchport',f' ip address {host(lookup["E",99],3+c)} {lookup["E",99]["mask"]}',' no shutdown','exit','interface range GigabitEthernet1/0/13-23',' shutdown','exit','interface range GigabitEthernet1/1/1-4',' shutdown','exit']
 write(f'configs/{name}.txt',end(lines))
for b in BUILDINGS:
 ss=[s for s in subnets if s['building']==b]; vids=','.join(str(s['vlan']) for s in ss)
 for d in (1,2):
  name=f'DIST-{b}{d}'; lines=common(name)
  lines += ['interface GigabitEthernet0/2',' description DOT1Q_TO_LOCAL_ACCESS',' no ip address',' no shutdown','exit','interface GigabitEthernet0/2.998',' encapsulation dot1Q 998 native',' no ip address','exit']
  for s in ss:
   if s['role']!='management':
    acl=f'{b}-V{s["vlan"]}-IN'; lines += [f'ip access-list extended {acl}']+[' '+r for r in acls[acl]]+['exit']
   lines += [f'interface GigabitEthernet0/2.{s["vlan"]}',f' encapsulation dot1Q {s["vlan"]}',f' description {b}_{s["name"]}',f' ip address {s[f"dist{d}"]} {s["mask"]}',f' standby {s["vlan"]} ip {s["vip"]}',f' standby {s["vlan"]} priority {110 if d==1 else 100}',f' standby {s["vlan"]} preempt']
   if s['dhcp_start']: lines += [f' ip helper-address {DHCP}']
   if s['role']!='management': lines += [f' ip access-group {b}-V{s["vlan"]}-IN in']
   lines += [' no shutdown','exit']
  lines += routing(name)
  write(f'configs/{name}.txt',end(lines))
 for a in (1,2):
  name=f'ACC-{b}{a}'; lines=common(name,False)+['spanning-tree mode rapid-pvst',f'spanning-tree vlan {vids} priority {4096 if a==1 else 8192}']
  for s in ss: lines += [f'vlan {s["vlan"]}',f' name {s["name"]}','exit']
  lines += ['vlan 998',' name NATIVE_UNUSED','exit','vlan 999',' name PARKING','exit','ip dhcp snooping',f'ip dhcp snooping vlan {vids}','no ip dhcp snooping information option',f'interface Vlan99',f' ip address {host(lookup[b,99],10+a)} {lookup[b,99]["mask"]}',' no shutdown','exit',f'ip default-gateway {lookup[b,99]["vip"]}']
  for d in (1,2):
   lines += [f'interface GigabitEthernet0/{d}',f' description {"TO_DIST_"+b+str(a) if d==1 else "TO_PEER_ACCESS"}',' switchport mode trunk',' switchport trunk native vlan 998',f' switchport trunk allowed vlan {vids},998',' switchport nonegotiate',' ip dhcp snooping trust',' no shutdown','exit']
  used={}
  for l in links:
   if l['b']==name and l['kind'].startswith('access:'): used[l['b_port']]=(int(l['kind'].split(':')[1]),l['a'])
  for p in range(1,25):
   port=f'FastEthernet0/{p}'; lines += [f'interface {port}',' switchport mode access']
   if port not in used: lines += [' description UNUSED_PARKED',' switchport access vlan 999',' shutdown','exit']; continue
   vid,peer=used[port]
   lines += [f' description TO_{peer}',f' switchport access vlan {vid}',' spanning-tree portfast',' spanning-tree bpduguard enable',' switchport port-security',' switchport port-security maximum 1',' switchport port-security mac-address sticky',' switchport port-security violation restrict']
   if peer=='DHCP-1': lines += [' ip dhcp snooping trust']
   else: lines += [' ip dhcp snooping limit rate 15']
   lines += [' no shutdown','exit']
  write(f'configs/{name}.txt',end(lines))

lines=common('DHCP-1')+['interface GigabitEthernet0/0',f' ip address {DHCP} {server["mask"]}',' no shutdown','exit',f'ip route 0.0.0.0 0.0.0.0 {server["vip"]}']
for s in subnets:
 if s['dhcp_start']:
  n=ip.ip_network(s['network'])
  lines += [f'ip dhcp excluded-address {s["first_host"]} {n.network_address+15}',f'ip dhcp pool {s["building"]}_V{s["vlan"]}',f' network {n.network_address} {s["mask"]}',f' default-router {s["vip"]}',f' dns-server {DNS}',' domain-name campus.example','exit']
lines += ['interface range GigabitEthernet0/1-2',' shutdown','exit']
write('configs/DHCP-1.txt',end(lines))
lines=common('EDGE')+routing('EDGE')+['interface Loopback99',' ip address 10.255.254.30 255.255.255.255','exit','interface GigabitEthernet0/0',' ip nat inside','exit','interface GigabitEthernet0/1',' ip nat inside','exit','interface GigabitEthernet0/2',' description SIMULATED_ISP',' ip address 198.51.100.1 255.255.255.252',' ip nat outside',' no shutdown','exit','ip access-list standard NAT-CAMPUS']
for _,(_,second,_) in BUILDINGS.items(): lines += [f' permit 10.{second}.0.0 0.0.255.255']
lines += ['exit','ip nat inside source list NAT-CAMPUS interface GigabitEthernet0/2 overload','ip route 0.0.0.0 0.0.0.0 198.51.100.2']
write('configs/EDGE.txt',end(lines))
# ISP is outside the campus trust domain; console only, no remote management advertised.
write('configs/ISP.txt',end(['enable','configure terminal','hostname ISP','no ip domain-lookup','enable secret LabOnly26Enable9','interface GigabitEthernet0/0',' ip address 198.51.100.2 255.255.255.252',' no shutdown','exit','interface GigabitEthernet0/1',' ip address 203.0.113.1 255.255.255.0',' no shutdown','exit','interface GigabitEthernet0/2',' shutdown','exit','line vty 0 4',' transport input none','exit']))

model=dict(schema_version=1,growth_factor=1.25,reserved_hosts_per_subnet=15,buildings={b:{'name':v[0],'allocation':f'10.{v[1]}.0.0/16'} for b,v in BUILDINGS.items()},subnets=subnets,nodes=nodes,links=links,endpoints=endpoints,services={'dhcp':DHCP,'dns':DNS,'educational_web':WEB,'it_admin':IT,'public_web':PUBLIC,'dns_records':{'edu.campus.example':WEB,'www.external.example':PUBLIC}},acls=acls,validation_status='STATIC_DESIGN_ONLY_NOT_SIMULATOR_TESTED')
write('design/campus.json',json.dumps(model,indent=2,ensure_ascii=False)+'\n')
csvfile('design/addressing_plan.csv',subnets)
csvfile('design/port_map.csv',links)
csvfile('design/devices.csv',nodes)
csvfile('design/endpoints.csv',endpoints)
csvfile('design/vlan_matrix.csv',[dict(vlan=v,**{b:lookup[b,v]['name'] if (b,v) in lookup else '-' for b in BUILDINGS}) for v in sorted({s['vlan'] for s in subnets})])
print(f'Generated {len(subnets)} subnets, {len(nodes)} device configs, {len(links)} links, {len(endpoints)} representative endpoints.')
print('No Packet Tracer tests have been executed by this generator.')
