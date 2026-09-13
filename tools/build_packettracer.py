#!/usr/bin/env python3
"""Build the native campus PKT. Opening/booting and runtime tests are separate gates.

Uses MIT-licensed tracketpacin helpers (see pt_vendor/LICENSE), with native models
from the installed Packet Tracer examples. No Cisco login/session data is used.
Requires: Python 3.10+, twofish. No automatic package installation is performed.
"""
import copy
import json
from pathlib import Path
import random
import sys
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/pt_vendor'))
import core
import ptexplorer as codec
codec._attempt_install=lambda package: False
core.EXTRA_TEMPLATE_SOURCES=[str(ROOT/'tools/pt_vendor/templates.xml')]
m=json.loads((ROOT/'design/campus.json').read_text())

class CampusLab(core.Lab):
 def _pick_template(self,requested_type,template_map):
  model=requested_type.split(':',1)[1]
  for candidates in template_map.values():
   for template in candidates:
    typ=template.find('ENGINE/TYPE')
    if typ is not None and typ.get('model')==model:
     return template
  # PC and Server native templates are sometimes stored without a model attribute.
  if model in ('Pc','Server'):
   key='pc' if model=='Pc' else 'server'
   return template_map[key][0]
  raise ValueError('Missing exact native model: '+model)

lab=CampusLab(random.Random(20260913));lab._min_separation=75
positions={'CORE-1':(650,60),'CORE-2':(1100,60),'EDGE':(1580,50),'ISP':(1750,50),'DHCP-1':(1690,300),'PUBLIC-WEB':(1750,175)}
for i,b in enumerate('ABCDE'):
 x=180+i*330
 positions.update({f'DIST-{b}1':(x-65,175),f'DIST-{b}2':(x+65,175),f'ACC-{b}1':(x-65,310),f'ACC-{b}2':(x+65,310)})
 lab.add_site_label(f'BUILDING {b} | {m["buildings"][b]["name"]}\n{m["buildings"][b]["allocation"]}',(x-140,115))
 ends=[e for e in m['endpoints'] if e['building']==b]
 for j,e in enumerate(ends): positions[e['name']]=(x-105+(j%3)*105,445+(j//3)*95)
for n in m['nodes']:
 name=n['name'];dtype=('switch:' if n['model'].startswith(('3650','2960')) else 'router:')+n['model']
 lines=(ROOT/f'configs/{name}.txt').read_text().splitlines()
 lines=[line for line in lines if line not in ('enable','configure terminal','write memory')]
 cfg='\n'.join(lines)
 core.PROFILE_LIBRARY[name]={'device_type':dtype.split(':')[0],'running_config':cfg,'startup_config':cfg}
 lab.add_device(name,dtype,position=positions[name],profile=name)
for e in m['endpoints']:
 server=e['role'] in ('dns','web','external')
 lab.add_device(e['name'],'server:Server' if server else 'pc:Pc',position=positions[e['name']])
for l in m['links']:
 lab.add_link(l['a'],l['a_port'],l['b'],l['b_port'])
lab.add_site_label('CORE / OSPF AREA 0',(550,5))
lab.add_site_label('DISTRIBUTION / 802.1Q + HSRP + ACL',(70,220))
lab.add_site_label('ACCESS / VLAN + L2 SECURITY',(70,355))
lab.add_site_label('DIST-X1: HSRP Active 110 | DIST-X2: Standby 100\nAccess X1 is STP root. See test_matrix.csv for recorded runtime results.',(440,810))
xmlpath=ROOT/'pt/university.xml'
lab.to_packettracer_xml(str(xmlpath))
tree=ET.parse(xmlpath);root=tree.getroot();devs=root.findall('NETWORK/DEVICES/DEVICE');ends={e['name']:e for e in m['endpoints']}

def settext(parent,path,text):
 element=parent
 for part in path.split('/'):
  child=element.find(part)
  if child is None: child=ET.SubElement(element,part)
  element=child
 element.text=str(text)
 return element

for index,dev in enumerate(devs,1):
 engine=dev.find('ENGINE');name=engine.findtext('NAME')
 # The helper randomizes port MACs, but the bridge base identity must also be unique.
 if engine.find('BUILD_IN_ADDR') is not None: settext(engine,'BUILD_IN_ADDR',f'02CA.0000.{index*256:04X}')
 settext(engine,'POWER','true')
 if name.startswith('ACC-'):
  # VLANs live in vlan.dat, not merely RUNNINGCONFIG. Native PT restores this
  # serialized database after parsing startup text; populate it explicitly.
  vlans=engine.find('VLANS')
  if vlans is None: vlans=ET.SubElement(engine,'VLANS')
  vlans.clear()
  defaults={1:'default',1002:'fddi-default',1003:'token-ring-default',1004:'fddinet-default',1005:'trnet-default',998:'NATIVE_UNUSED',999:'PARKING'}
  defaults.update({s['vlan']:s['name'] for s in m['subnets'] if s['building']==name[4]})
  for vid,label in sorted(defaults.items()): ET.SubElement(vlans,'VLAN',number=str(vid),name=label,rspan='0')
 if name not in ends: continue
 e=ends[name];dynamic=e['ip']=='DHCP'
 settext(engine,'GATEWAY','' if dynamic else e['gateway'])
 settext(engine,'DNS_CLIENT/SERVER_IP','' if dynamic else e['dns'])
 port=engine.find('.//PORT')
 settext(port,'IP','' if dynamic else e['ip']);settext(port,'SUBNET','' if dynamic else e['mask'])
 settext(port,'PORT_GATEWAY','' if dynamic else e['gateway']);settext(port,'PORT_DNS','' if dynamic else e['dns'])
 settext(port,'PORT_DHCP_ENABLE','true' if dynamic else 'false')
 settext(port,'POWER','true')
 if e['role'] in ('dns','web','external'):
  # Prevent services inherited from templates becoming rogue DHCP/management services.
  for service in ('DHCP_SERVER','TFTP_SERVER','NTP_SERVER','SYSLOG_SERVER','ACS_SERVER'):
   if engine.find(service) is not None: settext(engine,service+'/ENABLED','0')
  settext(engine,'DNS_SERVER/ENABLED','1' if e['role']=='dns' else '0')
  db=engine.find('DNS_SERVER/NAMESERVER-DATABASE')
  if db is None: db=ET.SubElement(engine.find('DNS_SERVER'),'NAMESERVER-DATABASE')
  db.clear()
  if e['role']=='dns':
   for domain,addr in m['services']['dns_records'].items():
    record=ET.SubElement(db,'RESOURCE-RECORD')
    for tag,value in [('TYPE','A-REC'),('NAME',domain),('TTL','3600'),('IPADDRESS',addr)]: settext(record,tag,value)
  for service in ('HTTP_SERVER','HTTPS_SERVER'):
   settext(engine,service+'/ENABLED','1' if e['role'] in ('web','external') else '0')
  if e['role'] in ('web','external'):
   for file in engine.findall('.//FILE'):
    if file.findtext('NAME')=='index.html':
     title='University Educational Portal' if e['role']=='web' else 'Simulated Internet Test Server'
     page=f'<html><body bgcolor="#edf3f8"><h1>{title}</h1><p>University Campus Network - Network Analysis and Design</p><p>This page is served by the simulated network, not a screenshot.</p></body></html>'
     settext(file,'FILE_CONTENT/TEXT',page)
# No trace of example network traffic is claimed as evidence for this new network.
for tag in ('PACKETANIMATION','PDU_LIST','SIMULATION_EVENT_LIST'):
 for element in root.findall('.//'+tag): element.clear()
ET.indent(tree,space=' ');tree.write(xmlpath,encoding='utf-8',short_empty_elements=False)
codec.ptfile_encode(str(xmlpath),str(ROOT/'pt/university.pkt'))
# Check encoding round trip, exact graph size, hardware identities and links.
raw=(ROOT/'pt/university.pkt').read_bytes();decoded=codec._decode_modern(raw)
assert decoded==xmlpath.read_bytes()
assert len(devs)==len(m['nodes'])+len(m['endpoints'])
refs={d.findtext('ENGINE/SAVE_REF_ID') for d in devs};assert len(refs)==len(devs)
for link in root.findall('NETWORK/LINKS/LINK'):
 assert link.findtext('CABLE/FROM') in refs and link.findtext('CABLE/TO') in refs
identities=[d.findtext('ENGINE/BUILD_IN_ADDR') for d in devs if d.find('ENGINE/BUILD_IN_ADDR') is not None]
assert len(identities)==len(set(identities))
result={'format_roundtrip':'PASS','devices':len(devs),'links':len(m['links']),'bridge_mac_uniqueness':'PASS','runtime_status':'NOT_PROVEN_BY_GENERATOR','model_source':'design/campus.json'}
(ROOT/'tests/pkt_structure_validation.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
