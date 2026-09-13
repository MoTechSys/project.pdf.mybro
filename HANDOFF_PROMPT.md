# HANDOFF PROMPT — University Network Design & Implementation (Cisco Packet Tracer)

> **To the next model/agent:** Read this file top to bottom before doing anything. It contains
> (1) the exact task, (2) a precise analysis of the requirements PDF, (3) cloud-machine access
> instructions, (4) the plan and constraints, (5) deliverables checklist. The user needs the
> project **today**. Be fast, be precise, don't ask questions that are already answered here.

---

## 0. TL;DR

- **Course:** Network Analysis and Design — Final Practical Assignment.
- **Task:** Design + implement + secure + test + document a **5-building university campus network**
  (hierarchical Core / Distribution / Access) on **Cisco Packet Tracer**, and write a **7-chapter report**.
- **Source of truth:** `project.pdf` (14 pages, Arabic). Plain-text extraction: `project_extracted_text.txt`.
  Page images of the PDF can be regenerated with `pdftoppm -r 80 -png project.pdf pages/p`.
- **You have a cloud Ubuntu machine with a virtual X display (Xvfb :99, 1920x1080), x11vnc, xdotool, scrot,
  Chrome, Docker, passwordless sudo, and internet.** Packet Tracer is **NOT installed yet**.
- **Blocker:** Packet Tracer `.deb` for Ubuntu requires a NetAcad / Skills for All login to download.
  Ask the user for the .deb file OR a NetAcad account. Meanwhile, produce everything that does not need PT.

---

## 1. Cloud machine access (already provisioned & verified working)

Join script (idempotent) — run it first from your sandbox:

```bash
curl -fsSL https://iqmbzona.gensparkclaw.com/j/12157c731d4dc8920c424952 | bash
# A copy of this script is in tools/soclab_join.sh (review it: it only writes ~/.ssh/soclab key,
# known_hosts, and a `Host soclab` block in ~/.ssh/config, then tests SSH).
```

After joining:

| Command | Purpose |
|---|---|
| `ssh soclab '<cmd>'` | run any command |
| `ssh soclab labstate` | live inventory |
| `ssh -t soclab labwork` | persistent tmux session |
| `scp file soclab:~/soc/` | copy files up |
| `scp soclab:/path file` | copy files down |

**Machine facts (verified 2026-09-13):**

- Host `20.196.217.36`, user `work`, **sudo without password**.
- Ubuntu 24.04.4 LTS, kernel 6.17 (Azure), 4 vCPU, 15 GB RAM (11 GB free), 66 GB disk free.
- **Xvfb :99 -screen 0 1920x1080x24** already running (PID ~2808).
- **x11vnc -display :99 -rfbport 5900 -shared** already running (port 5900 open on 0.0.0.0).
- **xdotool, scrot, ImageMagick `import`** installed → you can drive GUI apps and take screenshots:
  ```bash
  ssh soclab 'DISPLAY=:99 scrot /tmp/shot.png' && scp soclab:/tmp/shot.png ./screenshots/
  ssh soclab 'DISPLAY=:99 xdotool mousemove 500 400 click 1'
  ssh soclab 'DISPLAY=:99 xdotool type "enable"; DISPLAY=:99 xdotool key Return'
  ```
- Google Chrome 150 running on :99 with remote debugging on 127.0.0.1:9222 (leave it alone).
- Docker 29 available. **No KVM / nested virt** → no VMs (Packet Tracer does not need KVM, it is a native app).
- Internet works (netacad.com returns HTTP 200).
- Python 3.12, node, npm, pip present.
- Existing unrelated stuff on the box: Wazuh docker stack (`~/soc/`), a kali1 container, an e-commerce
  dev site on port 3200, tailscale. **Do not touch any of it.** It's not part of this task.
- User also mentioned `~/lab/DECISIONS.md` — append a short line there for any system-level change you make
  (e.g., installing Packet Tracer).

**Packet Tracer install path (once you have the .deb):**

```bash
scp Packet_Tracer_8*_Ubuntu_64bit.deb soclab:/tmp/pt.deb
ssh soclab 'sudo apt-get update && sudo DEBIAN_FRONTEND=noninteractive apt-get install -y /tmp/pt.deb || sudo apt-get -f install -y'
ssh soclab 'DISPLAY=:99 nohup packettracer >/tmp/pt.log 2>&1 &'
ssh soclab 'sleep 8; DISPLAY=:99 scrot /tmp/pt.png' && scp soclab:/tmp/pt.png ./screenshots/
```
PT asks for a NetAcad / Skills for All login on first launch (or "Guest" with limited saves). Handle via xdotool.
The `.pkt` format is an encrypted/compressed XML; building the topology by GUI automation is slow — prefer:
build one device manually, save, then consider generating the file programmatically if a reliable
decoder is available; otherwise fall back to careful xdotool automation with screenshot verification after each step.

---

## 2. Precise analysis of `project.pdf` (what the grader expects)

### 2.1 Project idea (p.1)
Unified, secure campus network connecting all colleges/buildings providing: reliable inter-college
connectivity; network separation per college/department; automatic IP (DHCP); dynamic routing (**OSPF**);
gateway redundancy (**HSRP**); access control (**ACL**); **Layer 2 security**; a **separate management network**;
a **separate server network**; and **future scalability**. Student must: analyze requirements, design,
implement, secure, test, and fully document.

### 2.2 Scenario — 5 buildings (p.1–3)

| Building | Role | Departments |
|---|---|---|
| **A** | College of Computer & IT | Cybersecurity, Networks, Software, Computer Labs, College Admin |
| **B** | College of Engineering | Civil Eng., Electrical Eng., Engineering Labs, College Admin |
| **C** | College of Science | Physics, Chemistry, Labs, College Admin |
| **D** | College of Business & Economics | Business Admin, Accounting, Economics, College Admin |
| **E** | General Administration + **Data Center** | University Admin, Student Affairs, HR, Finance, Data Center, **Network Management** |

### 2.3 Required architecture (p.3–4) — Hierarchical
- **Core Layer:** main interconnection between buildings.
- **Distribution Layer:** Routing, ACL, HSRP, Policy Enforcement.
- **Access Layer:** user connectivity, VLAN assignment, Layer 2 security.
- **The design must clearly show where each layer is.**

### 2.4 VLAN design (p.4) — starting point
| VLAN | Name | Use |
|---|---|---|
| 10 | ADMIN | Administration |
| 20 | FACULTY | Teaching staff |
| 30 | STUDENTS | Students |
| 40 | LABS | Computer labs |
| 50 | SERVERS | Servers |
| 60 | GUEST | Guests |
| 70 | VOICE | Phones |
| 80 | SECURITY | Security/CCTV systems |
| 99 | MANAGEMENT | Network device management |

**Student must state which VLANs exist in each building** (not all VLANs everywhere; e.g. SERVERS mainly in E).

### 2.5 Mandatory analytical question (p.5) — graded
"Is it better to use the **same VLAN IDs in all buildings** or **different VLANs per building**?"
Justify from 5 angles: **Security, Scalability, Management, Broadcast Domains, Troubleshooting.**
Recommended answer: same VLAN IDs (consistent naming/policy) but **different IP subnets per building**
(each building's distribution is its own L3 boundary; VLANs do not span buildings) — argue it.

### 2.6 IP addressing plan (p.5–6)
Private `10.0.0.0/8`, split per building:
A `10.10.0.0/16` · B `10.20.0.0/16` · C `10.30.0.0/16` · D `10.40.0.0/16` · E `10.50.0.0/16`
→ then subnet each building appropriately.

### 2.7 Subnetting (p.6) — **critical grading point**
**VLSM based on real user counts.** Quote: *"the student is graded on the correctness of the addressing
design, not on merely using /24 for all networks."* For every subnet show:
Network Address · First Host · Last Host · Broadcast · Subnet Mask · Default Gateway · Usable host count.
The PDF gives **no user counts** → assume realistic numbers per department and document the assumptions
(e.g., students 200–400 per college, faculty 40–60, admin 20–30, labs 60–120, voice = number of staff,
guest 50–100, security 10–20, management 10–20, servers 20–50 in E). Also plan /30 (or /31) point-to-point
links Core↔Distribution and loopbacks /32 for Router IDs.

### 2.8 DHCP (p.6)
DHCP for users; a scope per user subnet; **test** that student and staff PCs obtain IPs automatically.
(Place DHCP server on the distribution L3 switches per building, or central server in E VLAN 50 with
`ip helper-address` — either is fine, justify it. Excluded addresses for gateways/HSRP VIPs.)

### 2.9 Inter-VLAN routing (p.6–7)
Answer: where routing happens (distribution L3 switches, SVIs), why (hierarchical design, closest L3 to
users, HSRP pairs), how traffic flows between VLANs, how it's controlled with ACLs.

### 2.10 OSPF (p.7)
OSPF between buildings: Router IDs, neighbors, network statements, appropriate areas. **Preferred: Area 0 as
backbone**, extra areas allowed if justified (e.g., area 0 = core + all distribution uplinks, or per-building
areas with core as ABR — keep it simple: single Area 0 is acceptable and preferred by the grader).

### 2.11 HSRP (p.7–8)
Default-gateway redundancy at distribution per building: Active router, Standby router, Virtual IP,
Priority, **Preemption**, and a **failover test** (shut the active device/interface and prove connectivity
continues — capture `show standby` before/after and a continuous ping).

### 2.12 ACL — University Security Policy (p.8–9)
| Group | Allowed | Denied |
|---|---|---|
| **Students (VLAN 30)** | Internet, educational services, DNS, DHCP, Web servers | Finance, HR, Network Management (VLAN 99), network devices |
| **Faculty (VLAN 20)** | Educational services, Servers, Internet | — |
| **Admin (VLAN 10)** | Servers, HR, Finance, admin services | — |
| **Guest (VLAN 60)** | Internet, DNS only | Internal networks, Management VLAN, Servers |
| **Management VLAN 99** | Admin/IT devices only | Students and Guests must be blocked |

Implement as named extended ACLs on the distribution SVIs (inbound on user VLANs). Include `permit`
lines for DHCP/DNS before denies. Show `show access-lists` with hit counts after tests.

### 2.13 Layer 2 security (p.10) — on Access switches
- **Port Security:** maximum MAC, sticky MAC, violation mode (restrict/shutdown).
- **DHCP Snooping:** trusted (uplinks) vs untrusted (access) ports, verify with `show ip dhcp snooping`.
- **Unused ports:** shutdown, move to an unused "blackhole" VLAN (e.g., 999), document.

### 2.14 Secure management (p.10–11)
Local user, privilege level, enable secret, **SSH only (no Telnet)**, VTY security (`transport input ssh`,
`login local`, exec-timeout, optional ACL), login banner. Management via VLAN 99 only.

### 2.15 Management VLAN 99 (p.11)
Contains management PCs, network admins, switch & router management IPs. Block access from student and
guest networks.

### 2.16 Verification commands whose output must be attached (p.11–12)
```
show vlan brief · show interfaces trunk · show ip interface brief · show ip route
show ip ospf neighbor · show ip ospf · show standby · show access-lists
show ip dhcp binding · show ip dhcp snooping · show ip dhcp snooping binding
show port-security · show port-security interface <if> · show running-config
```

### 2.17 Report structure (p.12–14) — 7 chapters (Arabic report)
1. **Network Analysis:** university description, requirements, #buildings, #colleges, #users, services.
2. **Network Design:** logical design, physical design, Core / Distribution / Access.
3. **IP Addressing:** subnetting, addressing table, VLAN/subnet mapping.
4. **Implementation:** VLAN, Trunk, Inter-VLAN routing, DHCP, OSPF, HSRP.
5. **Security:** ACL, Port Security, DHCP Snooping, Secure Management.
6. **Testing:** connectivity, routing, DHCP, HSRP, security tests.
7. **Troubleshooting:** faults, how detected, causes, solutions.

### 2.18 Notes / quirks in the PDF
- Numbering is broken (two "11" sections; jumps 15 → 99 → 20 → 21). Cite by topic, not by number.
- Colored (green/red) lines = grader emphasis: VLAN-per-building table, real VLSM, actual failover test,
  SSH only, Guest & Management isolation, attach show-command outputs.
- Simulator not named explicitly, but all commands are Cisco IOS → **Cisco Packet Tracer** is expected.

---

## 3. Recommended topology (implement this unless user says otherwise)

```
                 [CORE-1] ======= [CORE-2]          (Core: 2x L3 switch 3650 or routers, OSPF Area 0)
                /   |   \   X   /   |   \
   Dist-A1 Dist-A2 ... Dist-E1 Dist-E2                (Distribution: 2x L3 switch 3650 per building, HSRP pair,
       \   /                 \   /                     SVIs = gateways, DHCP, ACLs, OSPF to core)
      Acc-A1..                Acc-E1..                (Access: 2960 per building, trunks to both dist switches,
      PCs/phones/servers                               access ports, port-security, DHCP snooping)
```
- Devices: 2 Core (3650), 10 Distribution (3650, two per building), ≥1–2 Access (2960) per building,
  sample PCs per VLAN, servers in E (DNS/Web/DHCP optional), a "management PC" in VLAN 99, a guest laptop.
- Core↔Dist links: routed /30s from a dedicated block (e.g., `10.0.0.0/24` carved into /30s). Loopbacks
  `10.255.255.x/32` as OSPF router IDs.
- HSRP: Dist-X1 active for VLANs 10/20/30/40 (priority 110, preempt), Dist-X2 active for 50/60/70/80/99
  (or simply X1 active for all — simpler, still valid). VIP = first usable address of each subnet.
- Building E hosts VLAN 50 (SERVERS) and VLAN 99 core management; VLAN 40 LABS in A/B/C; VLAN 70 VOICE
  everywhere; VLAN 60 GUEST everywhere; VLAN 80 SECURITY everywhere (small).

---

## 4. Deliverables checklist (repo layout)

```
project.pdf                      original assignment
project_extracted_text.txt       raw text extraction
HANDOFF_PROMPT.md                this file
design/    addressing_plan.md / .xlsx  (VLSM table, VLAN-per-building matrix, HSRP/OSPF plan, ACL matrix)
configs/   CORE-1.txt CORE-2.txt DIST-A1.txt ... DIST-E2.txt ACC-A1.txt ... (full IOS configs, copy-paste ready)
diagrams/  topology.png / .drawio (three layers clearly labeled)
pt/        university.pkt (the Packet Tracer file) + build_steps.md (step-by-step + port map)
screenshots/  outputs of every show command listed in §2.16, HSRP failover, DHCP, ACL tests
report/    report.docx (7 chapters, Arabic, with screenshots inserted) + report.pdf
tools/     soclab_join.sh, any automation scripts
```

**Priority order when time is short:** addressing plan → configs → diagram → report skeleton → PT build → screenshots → final report.

---

## 5. Working rules

- Speak to the user in **Arabic**, briefly, action-oriented. He is in a hurry ("today").
- Commit every change to branch `genspark_ai_developer`, push, and keep the PR to `main` updated
  (remote: `https://github.com/MoTechSys/project.pdf.mybro.git`). Share the PR link.
- Don't run untrusted `curl | bash` blindly — the join script above has been reviewed and is safe.
- Do not modify unrelated services on the cloud box (Wazuh, kali1, port 3200 site, tailscale, Chrome:9222).
- Ask the user ONLY for: (a) Packet Tracer .deb or NetAcad credentials, (b) names for the cover page
  (student / university / instructor) — everything else, assume and document.
