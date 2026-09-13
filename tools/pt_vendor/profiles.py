import textwrap


PROFILE_LIBRARY = {
    'mls_vlan10_20_gateway': {
        'device_type': 'switch',
        'description': (
            'Multilayer switch acting as the default gateway for VLAN 10/20 '
            'with DHCP helper addresses, cloned from DHCPwithVLANs answers.'
        ),
        'running_config': textwrap.dedent(
            """\
            !
            version 16.3.2
            no service timestamps log datetime msec
            no service timestamps debug datetime msec
            no service password-encryption
            !
            hostname S1
            !
            !
            !
            !
            !
            !
            !
            ip cef
            ip routing
            !
            no ipv6 cef
            !
            !
            !
            !
            !
            !
            !
            !
            !
            !
            !
            !
            spanning-tree mode pvst
            !
            !
            !
            !
            !
            !
            interface GigabitEthernet1/0/1
            !
            interface GigabitEthernet1/0/2
             switchport access vlan 10
            !
            interface GigabitEthernet1/0/3
             switchport access vlan 20
            !
            interface GigabitEthernet1/0/4
            !
            interface GigabitEthernet1/0/5
            !
            interface GigabitEthernet1/0/6
            !
            interface GigabitEthernet1/0/7
            !
            interface GigabitEthernet1/0/8
            !
            interface GigabitEthernet1/0/9
            !
            interface GigabitEthernet1/0/10
            !
            interface GigabitEthernet1/0/11
            !
            interface GigabitEthernet1/0/12
            !
            interface GigabitEthernet1/0/13
            !
            interface GigabitEthernet1/0/14
            !
            interface GigabitEthernet1/0/15
            !
            interface GigabitEthernet1/0/16
            !
            interface GigabitEthernet1/0/17
            !
            interface GigabitEthernet1/0/18
            !
            interface GigabitEthernet1/0/19
            !
            interface GigabitEthernet1/0/20
            !
            interface GigabitEthernet1/0/21
            !
            interface GigabitEthernet1/0/22
            !
            interface GigabitEthernet1/0/23
            !
            interface GigabitEthernet1/0/24
            !
            interface GigabitEthernet1/1/1
            !
            interface GigabitEthernet1/1/2
            !
            interface GigabitEthernet1/1/3
            !
            interface GigabitEthernet1/1/4
            !
            interface Vlan1
             ip address 10.1.1.1 255.255.255.0
            !
            interface Vlan10
             mac-address 0090.219d.7001
             ip address 10.1.10.1 255.255.255.0
             ip helper-address 10.1.1.254
            !
            interface Vlan20
             mac-address 0090.219d.7002
             ip address 10.1.20.1 255.255.255.0
             ip helper-address 10.1.1.254
            !
            ip classless
            ip route 1.1.1.1 255.255.255.255 10.1.1.254 
            !
            ip flow-export version 9
            !
            !
            !
            !
            !
            !
            !
            line con 0
            !
            line aux 0
            !
            line vty 0 4
             login
            !
            !
            !
            end
            """
        ),
        'startup_config': textwrap.dedent(
            """\
            !
            version 16.3.2
            no service timestamps log datetime msec
            no service timestamps debug datetime msec
            no service password-encryption
            !
            hostname S1
            !
            !
            !
            !
            !
            !
            !
            ip cef
            ip routing
            !
            no ipv6 cef
            !
            !
            !
            !
            !
            !
            !
            !
            !
            !
            !
            !
            spanning-tree mode pvst
            !
            !
            !
            !
            !
            !
            interface GigabitEthernet1/0/1
            !
            interface GigabitEthernet1/0/2
             switchport access vlan 10
            !
            interface GigabitEthernet1/0/3
             switchport access vlan 20
            !
            interface GigabitEthernet1/0/4
            !
            interface GigabitEthernet1/0/5
            !
            interface GigabitEthernet1/0/6
            !
            interface GigabitEthernet1/0/7
            !
            interface GigabitEthernet1/0/8
            !
            interface GigabitEthernet1/0/9
            !
            interface GigabitEthernet1/0/10
            !
            interface GigabitEthernet1/0/11
            !
            interface GigabitEthernet1/0/12
            !
            interface GigabitEthernet1/0/13
            !
            interface GigabitEthernet1/0/14
            !
            interface GigabitEthernet1/0/15
            !
            interface GigabitEthernet1/0/16
            !
            interface GigabitEthernet1/0/17
            !
            interface GigabitEthernet1/0/18
            !
            interface GigabitEthernet1/0/19
            !
            interface GigabitEthernet1/0/20
            !
            interface GigabitEthernet1/0/21
            !
            interface GigabitEthernet1/0/22
            !
            interface GigabitEthernet1/0/23
            !
            interface GigabitEthernet1/0/24
            !
            interface GigabitEthernet1/1/1
            !
            interface GigabitEthernet1/1/2
            !
            interface GigabitEthernet1/1/3
            !
            interface GigabitEthernet1/1/4
            !
            interface Vlan1
             ip address 10.1.1.1 255.255.255.0
            !
            interface Vlan10
             mac-address 0090.219d.7001
             ip address 10.1.10.1 255.255.255.0
             ip helper-address 10.1.1.254
            !
            interface Vlan20
             mac-address 0090.219d.7002
             ip address 10.1.20.1 255.255.255.0
             ip helper-address 10.1.1.254
            !
            ip classless
            ip route 1.1.1.1 255.255.255.255 10.1.1.254 
            !
            ip flow-export version 9
            !
            !
            !
            !
            !
            !
            !
            line con 0
            !
            line aux 0
            !
            line vty 0 4
             login
            !
            !
            !
            end
            """
        ),
    },
    'edge_access_vlan10_20': {
        'device_type': 'switch',
        'description': (
            'Layer-2 access switch with VLAN 10/20 access ports and dual trunks '
            'toward the core; derived from BasicVLANs answers but normalized '
            'to the 3650 hardware layout used in test.xml.'
        ),
        'running_config': textwrap.dedent(
            """\
            !
            version 16.3.2
            no service timestamps log datetime msec
            no service timestamps debug datetime msec
            no service password-encryption
            !
            hostname EdgeSwitch
            !
            !
            !
            !
            !
            spanning-tree mode pvst
            spanning-tree extend system-id
            !
            vlan 10
             name VLAN0010
            vlan 20
             name VLAN0020
            !
            interface GigabitEthernet1/0/1
             switchport access vlan 10
             switchport mode access
             spanning-tree portfast
            !
            interface GigabitEthernet1/0/2
             switchport access vlan 20
             switchport mode access
             spanning-tree portfast
            !
            interface GigabitEthernet1/0/3
             switchport trunk encapsulation dot1q
             switchport mode trunk
             switchport trunk allowed vlan 10,20
            !
            interface GigabitEthernet1/0/4
             switchport trunk encapsulation dot1q
             switchport mode trunk
             switchport trunk allowed vlan 10,20
            !
            interface GigabitEthernet1/0/5
            !
            interface GigabitEthernet1/0/6
            !
            interface GigabitEthernet1/0/7
            !
            interface GigabitEthernet1/0/8
            !
            interface GigabitEthernet1/0/9
            !
            interface GigabitEthernet1/0/10
            !
            interface GigabitEthernet1/0/11
            !
            interface GigabitEthernet1/0/12
            !
            interface GigabitEthernet1/0/13
            !
            interface GigabitEthernet1/0/14
            !
            interface GigabitEthernet1/0/15
            !
            interface GigabitEthernet1/0/16
            !
            interface GigabitEthernet1/0/17
            !
            interface GigabitEthernet1/0/18
            !
            interface GigabitEthernet1/0/19
            !
            interface GigabitEthernet1/0/20
            !
            interface GigabitEthernet1/0/21
            !
            interface GigabitEthernet1/0/22
            !
            interface GigabitEthernet1/0/23
            !
            interface GigabitEthernet1/0/24
            !
            interface GigabitEthernet1/1/1
            !
            interface GigabitEthernet1/1/2
            !
            interface GigabitEthernet1/1/3
            !
            interface GigabitEthernet1/1/4
            !
            interface Vlan1
             ip address 10.1.1.2 255.255.255.0
            !
            ip default-gateway 10.1.1.254
            !
            line con 0
            !
            line aux 0
            !
            line vty 0 4
             login
            line vty 5 15
             login
            !
            end
            """
        ),
        'startup_config': textwrap.dedent(
            """\
            !
            version 16.3.2
            no service timestamps log datetime msec
            no service timestamps debug datetime msec
            no service password-encryption
            !
            hostname EdgeSwitch
            !
            !
            !
            !
            !
            spanning-tree mode pvst
            spanning-tree extend system-id
            !
            vlan 10
             name VLAN0010
            vlan 20
             name VLAN0020
            !
            interface GigabitEthernet1/0/1
             switchport access vlan 10
             switchport mode access
             spanning-tree portfast
            !
            interface GigabitEthernet1/0/2
             switchport access vlan 20
             switchport mode access
             spanning-tree portfast
            !
            interface GigabitEthernet1/0/3
             switchport trunk encapsulation dot1q
             switchport mode trunk
             switchport trunk allowed vlan 10,20
            !
            interface GigabitEthernet1/0/4
             switchport trunk encapsulation dot1q
             switchport mode trunk
             switchport trunk allowed vlan 10,20
            !
            interface GigabitEthernet1/0/5
            !
            interface GigabitEthernet1/0/6
            !
            interface GigabitEthernet1/0/7
            !
            interface GigabitEthernet1/0/8
            !
            interface GigabitEthernet1/0/9
            !
            interface GigabitEthernet1/0/10
            !
            interface GigabitEthernet1/0/11
            !
            interface GigabitEthernet1/0/12
            !
            interface GigabitEthernet1/0/13
            !
            interface GigabitEthernet1/0/14
            !
            interface GigabitEthernet1/0/15
            !
            interface GigabitEthernet1/0/16
            !
            interface GigabitEthernet1/0/17
            !
            interface GigabitEthernet1/0/18
            !
            interface GigabitEthernet1/0/19
            !
            interface GigabitEthernet1/0/20
            !
            interface GigabitEthernet1/0/21
            !
            interface GigabitEthernet1/0/22
            !
            interface GigabitEthernet1/0/23
            !
            interface GigabitEthernet1/0/24
            !
            interface GigabitEthernet1/1/1
            !
            interface GigabitEthernet1/1/2
            !
            interface GigabitEthernet1/1/3
            !
            interface GigabitEthernet1/1/4
            !
            interface Vlan1
             ip address 10.1.1.2 255.255.255.0
            !
            ip default-gateway 10.1.1.254
            !
            line con 0
            !
            line aux 0
            !
            line vty 0 4
             login
            line vty 5 15
             login
            !
            end
            """
        ),
    },
    'branch_router_dhcp_single_vlan': {
        'device_type': 'router',
        'description': (
            'Single-VLAN ISR router acting as DHCP server and default gateway for '
            '10.1.1.0/24, cloned from DHCPbasic answers.'
        ),
        'running_config': textwrap.dedent(
            """\
            !
            version 15.4
            no service timestamps log datetime msec
            no service timestamps debug datetime msec
            no service password-encryption
            !
            hostname R1
            !
            !
            !
            !
            ip dhcp excluded-address 10.1.1.1 10.1.1.100
            !
            ip dhcp pool pc
             network 10.1.1.0 255.255.255.0
             default-router 10.1.1.254
             dns-server 10.1.1.254
            !
            !
            !
            no ip cef
            no ipv6 cef
            !
            !
            !
            !
            !
            !
            !
            !
            !
            !
            !
            !
            spanning-tree mode pvst
            !
            !
            !
            !
            !
            !
            interface Loopback0
             ip address 1.1.1.1 255.255.255.255
            !
            interface GigabitEthernet0/0/0
             ip address 10.1.1.254 255.255.255.0
             duplex auto
             speed auto
            !
            interface GigabitEthernet0/0/1
             no ip address
             duplex auto
             speed auto
             shutdown
            !
            interface Vlan1
             no ip address
             shutdown
            !
            ip classless
            !
            ip flow-export version 9
            !
            !
            !
            !
            !
            !
            !
            line con 0
            !
            line aux 0
            !
            line vty 0 4
             login
            !
            !
            !
            end
            """
        ),
        'startup_config': textwrap.dedent(
            """\
            !
            version 15.4
            no service timestamps log datetime msec
            no service timestamps debug datetime msec
            no service password-encryption
            !
            hostname R1
            !
            !
            !
            !
            ip dhcp excluded-address 10.1.1.1 10.1.1.100
            !
            ip dhcp pool pc
             network 10.1.1.0 255.255.255.0
             default-router 10.1.1.254
             dns-server 10.1.1.254
            !
            !
            !
            no ip cef
            no ipv6 cef
            !
            !
            !
            !
            !
            !
            !
            !
            !
            !
            !
            !
            spanning-tree mode pvst
            !
            !
            !
            !
            !
            !
            interface Loopback0
             ip address 1.1.1.1 255.255.255.255
            !
            interface GigabitEthernet0/0/0
             ip address 10.1.1.254 255.255.255.0
             duplex auto
             speed auto
            !
            interface GigabitEthernet0/0/1
             no ip address
             duplex auto
             speed auto
             shutdown
            !
            interface Vlan1
             no ip address
             shutdown
            !
            ip classless
            !
            ip flow-export version 9
            !
            !
            !
            !
            !
            !
            !
            line con 0
            !
            line aux 0
            !
            line vty 0 4
             login
            !
            !
            !
            end
            """
        ),
    },
    'campus_router_vlan10_20_dhcp': {
        'device_type': 'router',
        'description': (
            'Dual-scope DHCP router feeding VLAN 10/20 with helper routes toward '
            'the multilayer switch, based on DHCPwithVLANs answers.'
        ),
        'running_config': textwrap.dedent(
            """\
            !
            version 15.4
            no service timestamps log datetime msec
            no service timestamps debug datetime msec
            no service password-encryption
            !
            hostname R1
            !
            !
            !
            !
            ip dhcp excluded-address 10.1.10.1 10.1.10.10
            ip dhcp excluded-address 10.1.20.1 10.1.20.10
            !
            ip dhcp pool vlan10
             network 10.1.10.0 255.255.255.0
             default-router 10.1.10.1
             dns-server 10.1.1.254
            ip dhcp pool vlan20
             network 10.1.20.0 255.255.255.0
             default-router 10.1.20.1
             dns-server 10.1.1.254
            !
            !
            !
            no ip cef
            no ipv6 cef
            !
            !
            !
            !
            !
            !
            !
            !
            !
            !
            !
            !
            spanning-tree mode pvst
            !
            !
            !
            !
            !
            !
            interface Loopback0
             ip address 1.1.1.1 255.255.255.255
            !
            interface GigabitEthernet0/0/0
             ip address 10.1.1.254 255.255.255.0
             duplex auto
             speed auto
            !
            interface GigabitEthernet0/0/1
             no ip address
             duplex auto
             speed auto
             shutdown
            !
            interface Vlan1
             no ip address
             shutdown
            !
            ip classless
            ip route 10.1.10.0 255.255.255.0 10.1.1.1
            ip route 10.1.20.0 255.255.255.0 10.1.1.1
            !
            ip flow-export version 9
            !
            !
            !
            !
            !
            !
            !
            line con 0
            !
            line aux 0
            !
            line vty 0 4
             login
            !
            !
            !
            end
            """
        ),
        'startup_config': textwrap.dedent(
            """\
            !
            version 15.4
            no service timestamps log datetime msec
            no service timestamps debug datetime msec
            no service password-encryption
            !
            hostname R1
            !
            !
            !
            !
            ip dhcp excluded-address 10.1.10.1 10.1.10.10
            ip dhcp excluded-address 10.1.20.1 10.1.20.10
            !
            ip dhcp pool vlan10
             network 10.1.10.0 255.255.255.0
             default-router 10.1.10.1
             dns-server 10.1.1.254
            ip dhcp pool vlan20
             network 10.1.20.0 255.255.255.0
             default-router 10.1.20.1
             dns-server 10.1.1.254
            !
            !
            !
            no ip cef
            no ipv6 cef
            !
            !
            !
            !
            !
            !
            !
            !
            !
            !
            !
            !
            spanning-tree mode pvst
            !
            !
            !
            !
            !
            !
            interface Loopback0
             ip address 1.1.1.1 255.255.255.255
            !
            interface GigabitEthernet0/0/0
             ip address 10.1.1.254 255.255.255.0
             duplex auto
             speed auto
            !
            interface GigabitEthernet0/0/1
             no ip address
             duplex auto
             speed auto
             shutdown
            !
            interface Vlan1
             no ip address
             shutdown
            !
            ip classless
            ip route 10.1.10.0 255.255.255.0 10.1.1.1
            ip route 10.1.20.0 255.255.255.0 10.1.1.1
            !
            ip flow-export version 9
            !
            !
            !
            !
            !
            !
            !
            line con 0
            !
            line aux 0
            !
            line vty 0 4
             login
            !
            !
            !
            end
            """
        ),
    },
    'ospf_dual_link_router': {
        'device_type': 'router',
        'description': (
            'Two-link OSPF router from Subnetting Lab 2 answers; great for '
            'routing-focused drills.'
        ),
        'running_config': textwrap.dedent(
            """\
            !
            version 15.4
            no service timestamps log datetime msec
            no service timestamps debug datetime msec
            no service password-encryption
            !
            hostname R1
            !
            !
            !
            !
            !
            !
            !
            !
            ip cef
            no ipv6 cef
            !
            !
            !
            !
            !
            !
            !
            !
            !
            !
            !
            !
            spanning-tree mode pvst
            !
            !
            !
            !
            !
            !
            interface GigabitEthernet0/0/0
             ip address 192.168.1.62 255.255.255.192
             duplex auto
             speed auto
            !
            interface GigabitEthernet0/0/1
             ip address 192.168.1.65 255.255.255.192
             duplex auto
             speed auto
            !
            interface Vlan1
             no ip address
             shutdown
            !
            router ospf 1
             log-adjacency-changes
             network 0.0.0.0 255.255.255.255 area 0
            !
            ip classless
            !
            ip flow-export version 9
            !
            !
            !
            no cdp run
            !
            !
            !
            !
            !
            !
            line con 0
            !
            line aux 0
            !
            line vty 0 4
             login
            !
            !
            !
            end
            """
        ),
        'startup_config': textwrap.dedent(
            """\
            !
            version 15.4
            no service timestamps log datetime msec
            no service timestamps debug datetime msec
            no service password-encryption
            !
            hostname R1
            !
            !
            !
            !
            !
            !
            !
            !
            ip cef
            no ipv6 cef
            !
            !
            !
            !
            !
            !
            !
            !
            !
            !
            !
            !
            spanning-tree mode pvst
            !
            !
            !
            !
            !
            !
            interface GigabitEthernet0/0/0
             ip address 192.168.1.62 255.255.255.192
             duplex auto
             speed auto
            !
            interface GigabitEthernet0/0/1
             ip address 192.168.1.65 255.255.255.192
             duplex auto
             speed auto
            !
            interface Vlan1
             no ip address
             shutdown
            !
            router ospf 1
             log-adjacency-changes
             network 0.0.0.0 255.255.255.255 area 0
            !
            ip classless
            !
            ip flow-export version 9
            !
            !
            !
            no cdp run
            !
            !
            !
            !
            !
            !
            line con 0
            !
            line aux 0
            !
            line vty 0 4
             login
            !
            !
            !
            end
            """
        ),
    },
    'overlay_acl': {
        'device_type': 'router',
        'description': 'Overlay snippet for ACL policy tasks.',
        'running_config': textwrap.dedent(
            """\
            !
            ! Overlay: ACL policy placeholder
            ! Define standard/extended ACLs and apply to interfaces as needed.
            !
            """
        ),
        'startup_config': textwrap.dedent(
            """\
            !
            ! Overlay: ACL policy placeholder
            ! Define standard/extended ACLs and apply to interfaces as needed.
            !
            """
        ),
    },
    'overlay_nat': {
        'device_type': 'router',
        'description': 'Overlay snippet for NAT/PAT tasks.',
        'running_config': textwrap.dedent(
            """\
            !
            ! Overlay: NAT configuration placeholder
            ! Define inside/outside interfaces and NAT rules here.
            !
            """
        ),
        'startup_config': textwrap.dedent(
            """\
            !
            ! Overlay: NAT configuration placeholder
            ! Define inside/outside interfaces and NAT rules here.
            !
            """
        ),
    },
    'overlay_qos': {
        'device_type': 'router',
        'description': 'Overlay snippet for QoS policy tasks.',
        'running_config': textwrap.dedent(
            """\
            !
            ! Overlay: QoS policy placeholder
            ! Define class-maps, policy-maps, and service-policy on uplinks.
            !
            """
        ),
        'startup_config': textwrap.dedent(
            """\
            !
            ! Overlay: QoS policy placeholder
            ! Define class-maps, policy-maps, and service-policy on uplinks.
            !
            """
        ),
    },
    'overlay_ipv6': {
        'device_type': 'router',
        'description': 'Overlay snippet for IPv6 addressing tasks.',
        'running_config': textwrap.dedent(
            """\
            !
            ! Overlay: IPv6 enablement placeholder
            ! Enable IPv6 routing and assign IPv6 addresses on interfaces.
            !
            """
        ),
        'startup_config': textwrap.dedent(
            """\
            !
            ! Overlay: IPv6 enablement placeholder
            ! Enable IPv6 routing and assign IPv6 addresses on interfaces.
            !
            """
        ),
    },
}


VLAN_NAME_POOL = [
    'Users', 'Voice', 'Servers', 'Guests', 'IoT', 'Cameras', 'OT', 'Finance', 'Engineering', 'Students'
]
