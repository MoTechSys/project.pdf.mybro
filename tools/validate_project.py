#!/usr/bin/env python3
"""Independent static invariants and first-match IOS ACL evaluation. No live claims."""
import ipaddress as ip
import json
import re
from pathlib import Path
from datetime import datetime, timezone
ROOT=Path(__file__).resolve().parents[1]
m=json.loads((ROOT/'design/campus.json').read_text())
checks=[]
def check(name,condition,detail=''):
 checks.append({'name':name,'passed':bool(condition),'detail':detail})

def address(tokens,i):
 if tokens[i]=='any': return ip.ip_network('0.0.0.0/0'),i+1
 if tokens[i]=='host': return ip.ip_network(tokens[i+1]+'/32'),i+2
 return ip.ip_network(tokens[i]+'/'+tokens[i+1]),i+2

def evaluate(rules,src,dst,proto='tcp',sport=45000,dport=80,ack=False,icmp='echo'):
 for rule in rules:
  t=rule.split(); action,p=t[:2]
  source,i=address(t,2); sp=None; dp=None
  if i<len(t) and t[i]=='eq': sp=int(t[i+1]); i+=2
  dest,i=address(t,i)
  if i<len(t) and t[i]=='eq': dp=int(t[i+1]); i+=2
  tail=t[i:]
  if p not in ('ip',proto): continue
  if ip.ip_address(src) not in source or ip.ip_address(dst) not in dest: continue
  if sp is not None and sport!=sp: continue
  if dp is not None and dport!=dp: continue
  if 'established' in tail and not ack: continue
  if 'echo-reply' in tail and icmp!='echo-reply': continue
  return action
 return 'deny'

ss=m['subnets']; nets=[ip.ip_network(s['network']) for s in ss]; svc=m['services']
check('Five buildings and 46 subnets',len(m['buildings'])==5 and len(ss)==46)
check('VLSM has at least three prefix lengths',len({n.prefixlen for n in nets})>=3)
for i,s in enumerate(ss):
 n=nets[i]; name=f'{s["building"]}/VLAN{s["vlan"]}'
 check(name+' building allocation',n.subnet_of(ip.ip_network(m['buildings'][s['building']]['allocation'])))
 check(name+' no subnet overlap',all(not n.overlaps(other) for other in nets[i+1:]))
 check(name+' growth and reserved capacity',s['endpoint_capacity']>=s['growth_endpoints'] and s['usable']==n.num_addresses-2)
 check(name+' boundaries',s['first_host']==str(n.network_address+1) and s['last_host']==str(n.broadcast_address-1) and s['broadcast']==str(n.broadcast_address) and s['mask']==str(n.netmask))
 check(name+' distinct valid HSRP addresses',len({s['vip'],s['dist1'],s['dist2']})==3 and all(ip.ip_address(s[k]) in n for k in ('vip','dist1','dist2')))
 if s['dhcp_start']:
  start=ip.ip_address(s['dhcp_start']); last=ip.ip_address(s['dhcp_end'])
  check(name+' DHCP capacity and exclusion',int(last)-int(start)+1>=s['growth_endpoints'] and start==n.network_address+16)
  config=(ROOT/'configs/DHCP-1.txt').read_text()
  check(name+' DHCP correct virtual gateway',f'default-router {s["vip"]}' in config)
 for d in (1,2):
  cfg=(ROOT/f'configs/DIST-{s["building"]}{d}.txt').read_text()
  block=cfg.split(f'interface GigabitEthernet0/2.{s["vlan"]}\n')[1].split('\nexit')[0]
  check(name+f' HSRP peer {d}',f'standby {s["vlan"]} ip {s["vip"]}' in block and f'standby {s["vlan"]} priority {110 if d==1 else 100}' in block and f'standby {s["vlan"]} preempt' in block)
  if s['dhcp_start']: check(name+f' relay peer {d}',f'ip helper-address {svc["dhcp"]}' in block)
  if s['role']!='management':
   aclname=f'{s["building"]}-V{s["vlan"]}-IN'
   check(name+f' ACL application peer {d}',f'ip access-group {aclname} in' in block)
   configured=cfg.split(f'ip access-list extended {aclname}\n')[1].split('\nexit')[0]
   check(name+f' ACL content peer {d}',[x.strip() for x in configured.splitlines()]==m['acls'][aclname])

ports=[]; allips=[]
for l in m['links']:
 for side in ('a','b'): ports.append((l[side],l[side+'_port']))
 if l['network']:
  net=ip.ip_network(l['network'])
  check(f'{l["a"]}-{l["b"]} link addresses',l['a_ip']!=l['b_ip'] and ip.ip_address(l['a_ip']) in net and ip.ip_address(l['b_ip']) in net)
  if l['kind']=='routed':
   check(f'{l["a"]}-{l["b"]} transit distinct from VLANs',not any(net.overlaps(n) for n in nets))
  allips += [l['a_ip'],l['b_ip']]
check('Every physical interface used at most once',len(ports)==len(set(ports)))
check('Unique routed link addresses',len(allips)==len(set(allips)))
rids=[n['router_id'] for n in m['nodes'] if n['router_id']]
check('Unique OSPF router IDs',len(rids)==len(set(rids)))
for node in m['nodes']:
 name=node['name']; config=(ROOT/f'configs/{name}.txt').read_text()
 if name=='ISP': continue
 check(name+' SSH only and IT source restriction','transport input ssh' in config and 'transport input telnet' not in config and f'permit host {svc["it_admin"]}' in config and 'access-class VTY-IT in' in config)
 if node['layer'] in ('Core','Distribution','Border'):
  check(name+' passive default OSPF','passive-interface default' in config and f'router-id {node["router_id"]}' in config)
 if node['layer']=='Distribution':
  uplinks=[l for l in m['links'] if l['kind']=='routed' and name in (l['a'],l['b'])]
  check(name+' dual core paths',len(uplinks)==2)
 if node['layer']=='Access':
  check(name+' snooping enabled and Option82 choice','\nip dhcp snooping\n' in config and 'no ip dhcp snooping information option' in config)
  for port in range(1,25):
   block=config.split(f'interface FastEthernet0/{port}\n')[1].split('\nexit')[0]
   used=any(l['b']==name and l['b_port']==f'FastEthernet0/{port}' for l in m['links'])
   if used:
    check(name+f'/Fa0/{port} access protection','port-security mac-address sticky' in block and 'port-security maximum 1' in block and 'violation restrict' in block and 'bpduguard enable' in block)
    if 'TO_DHCP-1' in block: check(name+' DHCP source trusted','ip dhcp snooping trust' in block)
    else: check(name+f'/Fa0/{port} not trusted','ip dhcp snooping trust' not in block)
   else: check(name+f'/Fa0/{port} unused shutdown','switchport access vlan 999' in block and '\n shutdown' in block)

for s in ss:
 if s['role']=='management': continue
 acl=m['acls'][f'{s["building"]}-V{s["vlan"]}-IN']; src=str(ip.ip_network(s['network']).network_address+16); role=s['role']; name=f'{s["building"]}/V{s["vlan"]}'
 check(name+' DHCP discover permitted',evaluate(acl,'0.0.0.0','255.255.255.255','udp',68,67)=='permit')
 check(name+' DHCP renewal permitted',evaluate(acl,src,svc['dhcp'],'udp',68,67)=='permit')
 for proto in ('udp','tcp'): check(name+' DNS '+proto,evaluate(acl,src,svc['dns'],proto,45000,53)=='permit')
 for mg in [x for x in ss if x['role']=='management']:
  dest=str(ip.ip_network(mg['network']).network_address+10)
  check(name+' denied management '+mg['building'],evaluate(acl,src,dest,'tcp',45000,22)=='deny' and evaluate(acl,src,dest,'icmp')=='deny')
 if role in ('student','guest','faculty','voice','security'):
  for restricted in [x for x in ss if x['role'] in ('hr','finance')]:
   dst=str(ip.ip_network(restricted['network']).network_address+16)
   for proto,dp in [('tcp',80),('tcp',22),('udp',67),('icmp',0)]: check(name+f' denies {restricted["role"]}/{proto}/{dp}',evaluate(acl,src,dst,proto,68 if dp==67 else 45000,dp)=='deny')
 if role=='guest':
  check(name+' denies educational web',evaluate(acl,src,svc['educational_web'])=='deny')
  check(name+' denies other server ports',evaluate(acl,src,svc['dns'],'tcp',45000,80)=='deny')
 else: check(name+' permits educational web',evaluate(acl,src,svc['educational_web'])=='permit')
 check(name+' Internet policy',evaluate(acl,src,svc['public_web'])==('deny' if role in ('voice','security') else 'permit'))
 check(name+' denies spoofed cross-VLAN source',evaluate(acl,'10.123.45.67',svc['public_web'])=='deny')
 for v in ss:
  for k in ('vip','dist1','dist2'): check(name+f' denies device {v["building"]}/{v["vlan"]}/{k}',evaluate(acl,src,v[k],'tcp',45000,22)=='deny')
 # HSRP multicast must survive ingress filtering on both peers.
 for k in ('dist1','dist2'): check(name+' HSRP '+k,evaluate(acl,s[k],'224.0.0.2','udp',1985,1985)=='permit')

result={'kind':'STATIC_DESIGN_VALIDATION_NOT_PACKET_TRACER','passed':sum(x['passed'] for x in checks),'failed':sum(not x['passed'] for x in checks),'checks':checks}
out=ROOT/'tests'; out.mkdir(exist_ok=True)
(out/'validation_results.json').write_text(json.dumps(result,indent=2)+'\n')
print(f'Static checks: {result["passed"]} PASS; {result["failed"]} FAIL')
for c in checks:
 if not c['passed']: print('FAIL:',c['name'],c['detail'])
raise SystemExit(bool(result['failed']))
