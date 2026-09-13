import glob
import os
import random
import uuid
import xml.etree.ElementTree as ET

from profiles import PROFILE_LIBRARY


def _discover_template_sources():
    base_dir = os.path.dirname(__file__)
    patterns = [
        os.path.join(base_dir, 'examples', '*.xml'),
        os.path.join(base_dir, 'examples', 'more', '*.xml'),
    ]
    sources = []
    for pattern in patterns:
        sources.extend(glob.glob(pattern))
    return sources


EXTRA_TEMPLATE_SOURCES = [
    os.path.join('examples', 'DHCPbasicAnswers.xml'),
    os.path.join('examples', 'DHCPwithVLANsAnswers.xml'),
    os.path.join('examples', 'SubnettingLab2Answers.xml'),
]
EXTRA_TEMPLATE_SOURCES.extend(_discover_template_sources())


class Lab:
    """Build Packet Tracer topologies by cloning templates from test.xml."""

    def __init__(self, rng=None):
        self.devices = []
        self.links = []
        self._name_counts = {}
        self._instruction_note_text = None
        self._note_position = (1200, 140)
        self._note_mem_seed = random.randint(2582360000000, 2582369999999)
        self._site_labels = []
        self._device_lookup = {}
        self._link_cable_memory = {}
        self._occupied_positions = set()
        self._occupied_list = []
        self._min_separation = 100
        self._rng = rng or random.Random()
        self._used_macs = set()

    def unique_name(self, base):
        """Return a device name that is unique inside this lab."""
        sanitized = (base or 'Device').strip() or 'Device'
        existing = {dev['name'] for dev in self.devices}
        if sanitized not in existing:
            self._name_counts[sanitized] = 1
            return sanitized
        suffix = self._name_counts.get(sanitized, 1) + 1
        while True:
            candidate = f'{sanitized}{suffix}'
            if candidate not in existing:
                self._name_counts[sanitized] = suffix
                return candidate
            suffix += 1

    def set_instruction_note_text(self, text, position=None):
        """Store human instructions that will be embedded as a Packet Tracer note.

        Angle brackets are replaced with parentheses because ElementTree
        escapes them to ``&lt;``/``&gt;`` which Packet Tracer interprets as
        HTML markup, collapsing the note into a single line.
        """
        cleaned = text.strip() if text else None
        if cleaned:
            cleaned = cleaned.replace('<', '(').replace('>', ')')
        self._instruction_note_text = cleaned if cleaned else None
        if position:
            self._note_position = position

    def add_site_label(self, text, position, z=40000, cluster_id='1-1'):
        """Add a short label note to help organize large logical layouts."""
        cleaned = text.strip() if text else None
        if not cleaned:
            return
        self._site_labels.append({
            'text': cleaned,
            'position': position,
            'z': z,
            'cluster_id': cluster_id,
        })

    def add_device(self, name, device_type, position=None, profile=None):
        """Register a device, optional logical position, and config profile."""
        if any(device['name'] == name for device in self.devices):
            raise ValueError(f'Device name {name} already exists; use lab.unique_name() for collisions.')
        resolved_position = self._resolve_position(position)
        info = {
            'name': name,
            'type': device_type,
            'position': resolved_position,
            'profile': profile,
        }
        self.devices.append(info)
        self._device_lookup[name] = info
        return name

    def _resolve_position(self, position):
        if not position:
            return position
        x, y = position
        min_x = 100
        base = (max(min_x, int(x)), int(y))

        def is_clear(candidate):
            if candidate in self._occupied_positions:
                return False
            for other in self._occupied_list:
                if abs(candidate[0] - other[0]) < self._min_separation and abs(candidate[1] - other[1]) < self._min_separation:
                    return False
            return True

        if is_clear(base):
            self._occupied_positions.add(base)
            self._occupied_list.append(base)
            return base

        step = 20
        max_radius = 240
        for radius in range(step, max_radius + step, step):
            for dx in range(-radius, radius + step, step):
                for dy in range(-radius, radius + step, step):
                    if abs(dx) != radius and abs(dy) != radius:
                        continue
                    candidate = (max(min_x, base[0] + dx), base[1] + dy)
                    if is_clear(candidate):
                        self._occupied_positions.add(candidate)
                        self._occupied_list.append(candidate)
                        return candidate

        for dx in range(20, 121, 20):
            for dy in range(20, 121, 20):
                candidate = (max(min_x, base[0] + dx), base[1] + dy)
                if is_clear(candidate):
                    self._occupied_positions.add(candidate)
                    self._occupied_list.append(candidate)
                    return candidate

        self._occupied_positions.add(base)
        self._occupied_list.append(base)
        return base

    def _infer_cable_type(self, dev1, dev2):
        def categorize(dev_name):
            dev = self._device_lookup.get(dev_name) or {}
            dtype = (dev.get('type') or '').lower()
            if dtype.startswith('switch'):
                return 'switch'
            if dtype.startswith('router'):
                return 'router'
            if dtype.startswith('server'):
                return 'pc'
            return 'pc'

        cat1 = categorize(dev1)
        cat2 = categorize(dev2)
        if cat1 == cat2:
            return 'eCrossOver'
        return 'eStraightThrough'

    def add_link(self, dev1, port1, dev2, port2, length='5', cable_type=None):
        pair_key = frozenset({dev1, dev2})
        resolved_type = cable_type or self._infer_cable_type(dev1, dev2)
        if pair_key in self._link_cable_memory:
            resolved_type = self._link_cable_memory[pair_key]
        else:
            self._link_cable_memory[pair_key] = resolved_type

        self.links.append({
            'dev1': dev1,
            'port1': port1,
            'dev2': dev2,
            'port2': port2,
            'length': str(length),
            'cable_type': resolved_type,
        })

    def _generate_mac(self):
        while True:
            first = 0x02
            rest = [self._rng.randint(0x00, 0xFF) for _ in range(5)]
            raw = bytes([first] + rest)
            mac = ''.join(f'{b:02X}' for b in raw)
            dotted = f'{mac[0:4]}.{mac[4:8]}.{mac[8:12]}'
            if dotted not in self._used_macs:
                self._used_macs.add(dotted)
                return dotted

    def _randomize_device_macs(self, device_elem):
        for port in device_elem.findall('.//PORT'):
            mac_elem = port.find('MACADDRESS')
            bia_elem = port.find('BIA')
            if mac_elem is None and bia_elem is None:
                continue
            mac = self._generate_mac()
            if mac_elem is not None:
                mac_elem.text = mac
            if bia_elem is not None:
                bia_elem.text = mac

    def to_packettracer_xml(self, path):
        """Clone devices from test.xml so every generated file matches PT 8.2 layout."""
        template_path = os.path.join(os.path.dirname(__file__), 'test.xml')
        if not os.path.exists(template_path):
            raise FileNotFoundError('test.xml not found; place a Packet Tracer 8.2 file next to this script.')

        tree = ET.parse(template_path)
        root = tree.getroot()
        template_version = root.findtext('VERSION')

        network = root.find('NETWORK')
        if network is None:
            raise ValueError('NETWORK section missing in test.xml')

        devices_elem = network.find('DEVICES')
        if devices_elem is None:
            raise ValueError('DEVICES section missing in test.xml')

        template_map = self._collect_templates(devices_elem)
        self._ensure_extra_templates(template_map)
        devices_elem.clear()

        device_refs = {}
        layout_tracker = {'switch': 0, 'pc': 0, 'router': 0, 'server': 0}
        physical_tracker = {'rack': 0, 'pc': 0}

        for idx, dev_info in enumerate(self.devices):
            template = self._pick_template(dev_info['type'], template_map)
            new_device = self._deep_copy_element(template)
            self._assign_unique_save_ref(new_device)
            self._rename_device(new_device, dev_info['name'])
            self._position_device(new_device, dev_info, layout_tracker)
            self._clean_workspace(new_device, idx, physical_tracker)
            self._randomize_device_macs(new_device)
            if dev_info.get('profile'):
                self._apply_profile(new_device, dev_info)
            save_ref = self._extract_save_ref(new_device)
            device_refs[dev_info['name']] = save_ref
            devices_elem.append(new_device)

        links_elem = network.find('LINKS')
        if links_elem is None:
            links_elem = ET.SubElement(network, 'LINKS')
        links_elem.clear()

        for link in self.links:
            if link['dev1'] not in device_refs or link['dev2'] not in device_refs:
                continue
            link_elem = ET.SubElement(links_elem, 'LINK')
            ET.SubElement(link_elem, 'TYPE').text = 'eCopper'
            cable = ET.SubElement(link_elem, 'CABLE')
            ET.SubElement(cable, 'LENGTH').text = link['length']
            ET.SubElement(cable, 'FUNCTIONAL').text = 'true'
            ET.SubElement(cable, 'FROM').text = device_refs[link['dev1']]
            ET.SubElement(cable, 'PORT').text = link['port1']
            ET.SubElement(cable, 'TO').text = device_refs[link['dev2']]
            ET.SubElement(cable, 'PORT').text = link['port2']
            ET.SubElement(cable, 'TYPE').text = link['cable_type']

        self._rebuild_physical_workspace(root, devices_elem)
        self._inject_instruction_note(root)

        if template_version:
            version_elem = root.find('VERSION')
            if version_elem is not None:
                version_elem.text = template_version

        ET.indent(tree, space=' ')
        tree.write(path, encoding='utf-8', xml_declaration=False, short_empty_elements=False)
        print(f'Packet Tracer XML written to {path} using templates from test.xml')

    def _load_template_map(self):
        template_path = os.path.join(os.path.dirname(__file__), 'test.xml')
        if not os.path.exists(template_path):
            raise FileNotFoundError('test.xml not found; place a Packet Tracer 8.2 file next to this script.')
        tree = ET.parse(template_path)
        root = tree.getroot()
        network = root.find('NETWORK')
        if network is None:
            raise ValueError('NETWORK section missing in test.xml')
        devices_elem = network.find('DEVICES')
        if devices_elem is None:
            raise ValueError('DEVICES section missing in test.xml')
        template_map = self._collect_templates(devices_elem)
        self._ensure_extra_templates(template_map)
        return template_map

    def _collect_templates(self, devices_elem, template_map=None):
        if template_map is None:
            template_map = {'switch': [], 'pc': [], 'router': [], 'server': []}
        for device in devices_elem.findall('DEVICE'):
            category = self._categorize_device(device)
            if category:
                template_map[category].append(self._deep_copy_element(device))
        return template_map

    def _pick_template(self, requested_type, template_map):
        lowered = requested_type.lower()
        if lowered.startswith('switch'):
            bucket = 'switch'
        elif lowered.startswith('pc'):
            bucket = 'pc'
        elif lowered.startswith('router'):
            bucket = 'router'
        elif lowered.startswith('server'):
            bucket = 'server'
        else:
            raise ValueError(f'Unsupported device type: {requested_type}')

        templates = template_map.get(bucket, [])
        if not templates:
            raise ValueError(
                f'No templates available for {bucket}; ensure test.xml or EXTRA_TEMPLATE_SOURCES provide one.'
            )
        return templates[0]

    def _categorize_device(self, device_elem):
        dev_type = device_elem.findtext('ENGINE/TYPE', '').lower()
        if 'switch' in dev_type:
            return 'switch'
        if dev_type.startswith('pc'):
            return 'pc'
        if dev_type.startswith('server') or 'server' in dev_type:
            return 'server'
        if 'router' in dev_type:
            return 'router'
        return None

    def _ensure_extra_templates(self, template_map):
        base_dir = os.path.dirname(__file__)
        seen = set()
        for relative in EXTRA_TEMPLATE_SOURCES:
            extra_path = relative if os.path.isabs(relative) else os.path.join(base_dir, relative)
            if extra_path in seen:
                continue
            seen.add(extra_path)
            if not os.path.exists(extra_path):
                continue
            try:
                extra_tree = ET.parse(extra_path)
            except ET.ParseError:
                continue
            extra_root = extra_tree.getroot()
            network = extra_root.find('NETWORK')
            if network is None:
                continue
            devices_elem = network.find('DEVICES')
            if devices_elem is None:
                continue
            self._collect_templates(devices_elem, template_map)

    def _assign_unique_save_ref(self, device_elem):
        engine = device_elem.find('ENGINE')
        if engine is None:
            return
        save_ref = engine.find('SAVE_REF_ID')
        if save_ref is None:
            save_ref = ET.SubElement(engine, 'SAVE_REF_ID')
        unique_value = uuid.uuid4().int >> 64
        save_ref.text = f'save-ref-id:{unique_value}'

    def _rename_device(self, device_elem, new_name):
        engine = device_elem.find('ENGINE')
        if engine is None:
            return
        name_elem = engine.find('NAME')
        if name_elem is not None:
            name_elem.text = new_name
        sys_name = engine.find('SYS_NAME')
        if sys_name is not None:
            sys_name.text = new_name

    def _position_device(self, device_elem, dev_info, layout_tracker):
        workspace = device_elem.find('WORKSPACE')
        if workspace is None:
            return
        logical = workspace.find('LOGICAL')
        if logical is None:
            return
        x_elem = logical.find('X')
        y_elem = logical.find('Y')

        if dev_info.get('position'):
            x_val, y_val = dev_info['position']
        else:
            lowered = dev_info['type'].lower()
            if lowered.startswith('switch'):
                column = layout_tracker['switch']
                layout_tracker['switch'] += 1
                x_val = 220 + column * 220
                y_val = 220
            elif lowered.startswith('router'):
                column = layout_tracker['router']
                layout_tracker['router'] += 1
                x_val = 220 + column * 220
                y_val = 80
            elif lowered.startswith('server'):
                column = layout_tracker['server']
                layout_tracker['server'] += 1
                x_val = 220 + column * 220
                y_val = 380
            else:
                column = layout_tracker['pc']
                layout_tracker['pc'] += 1
                x_val = 220 + column * 220
                y_val = 520

        if x_elem is not None:
            x_elem.text = str(x_val)
        if y_elem is not None:
            y_elem.text = str(y_val)

    def _clean_workspace(self, device_elem, idx, physical_tracker):
        workspace = device_elem.find('WORKSPACE')
        if workspace is None:
            workspace = ET.SubElement(device_elem, 'WORKSPACE')
        logical = workspace.find('LOGICAL')
        if logical is None:
            logical = ET.SubElement(workspace, 'LOGICAL')
        physical = workspace.find('PHYSICAL')
        if physical is None:
            physical = ET.SubElement(workspace, 'PHYSICAL')
        physical_cpur = workspace.find('PHYSICAL_CPUR')
        if physical_cpur is None:
            physical_cpur = ET.SubElement(workspace, 'PHYSICAL_CPUR')

        for tag in ['X_PN', 'Y_PN', 'X', 'Y', 'SLOT', 'SUBSLOT', 'PARENT_PATH', 'CONTAINER_ID']:
            if physical_cpur.find(tag) is None:
                ET.SubElement(physical_cpur, tag)

        device_type = device_elem.findtext('ENGINE/TYPE', '')
        lowered = device_type.lower()
        is_pc = lowered.startswith('pc') or lowered.startswith('server')

        homerack_uuids = [
            '866b072e-a242-4700-afc2-0d37fe0a38ac',
            '0d9c4da0-a254-4b80-8ef1-0af23052ef86',
            '940bdc5d-0715-4851-9c7b-6b1143f2af14',
            '79d0e2b3-9fae-487a-bace-2862f6689a40',
        ]
        rack_uuid = 'f6f9f4d5-6f96-46ef-b2f9-2f831132fb17'

        device_uuid = str(uuid.uuid4())
        if is_pc:
            physical.text = ','.join([f'{{{u}}}' for u in homerack_uuids[:3] + [device_uuid]])
            parent_path = ','.join([f'{{{u}}}' for u in homerack_uuids[:3]])
            container_uuid = homerack_uuids[2]
            position_index = physical_tracker['pc']
            physical_tracker['pc'] += 1
            x_val = 80 + (position_index % 4) * 70
            y_val = 200 + (position_index // 4) * 55
            slot_val = str(position_index)
        else:
            sequence = homerack_uuids + [rack_uuid, device_uuid]
            physical.text = ','.join([f'{{{u}}}' for u in sequence])
            parent_path = ','.join([f'{{{u}}}' for u in homerack_uuids])
            container_uuid = rack_uuid
            position_index = physical_tracker['rack']
            physical_tracker['rack'] += 1
            x_val = 4 + (position_index % 10) * 4
            y_val = (position_index // 10) * 4
            slot_val = str(position_index)

        x_text = str(x_val)
        y_text = str(y_val)

        physical_cpur.find('X').text = x_text
        physical_cpur.find('Y').text = y_text
        physical_cpur.find('X_PN').text = x_text
        physical_cpur.find('Y_PN').text = y_text
        physical_cpur.find('SLOT').text = slot_val
        physical_cpur.find('SUBSLOT').text = '0'
        physical_cpur.find('PARENT_PATH').text = parent_path
        physical_cpur.find('CONTAINER_ID').text = f'{{{container_uuid}}}'

        mem_addr = logical.find('MEM_ADDR')
        if mem_addr is None:
            mem_addr = ET.SubElement(logical, 'MEM_ADDR')
        mem_addr.text = str(2582301551760 + idx * 100000)

        dev_addr = logical.find('DEV_ADDR')
        if dev_addr is None:
            dev_addr = ET.SubElement(logical, 'DEV_ADDR')
        dev_addr.text = str(2582299771936 + idx * 100000)

    def _rebuild_physical_workspace(self, root, devices_elem):
        physicalworkspace = root.find('PHYSICALWORKSPACE')
        if physicalworkspace is None:
            return

        homerack_uuids = [
            '866b072e-a242-4700-afc2-0d37fe0a38ac',
            '0d9c4da0-a254-4b80-8ef1-0af23052ef86',
            '940bdc5d-0715-4851-9c7b-6b1143f2af14',
            '79d0e2b3-9fae-487a-bace-2862f6689a40',
        ]
        rack_uuid = 'f6f9f4d5-6f96-46ef-b2f9-2f831132fb17'

        homerack = physicalworkspace.find('HOMERACK')
        if homerack is not None:
            homerack.text = ','.join([f'{{{u}}}' for u in homerack_uuids])

        for node in physicalworkspace.findall('.//NODE'):
            for tag in ('ICP_CSX', 'ICP_CSY'):
                tag_elem = node.find(tag)
                if tag_elem is not None:
                    node.remove(tag_elem)

        wiring_closet = self._find_node_by_name_and_type(physicalworkspace, 'Main Wiring Closet', '3')
        corporate_office = self._find_node_by_name_and_type(physicalworkspace, 'Corporate Office', '2')
        if wiring_closet is None or corporate_office is None:
            return

        wc_children = wiring_closet.find('CHILDREN')
        if wc_children is None:
            wc_children = ET.SubElement(wiring_closet, 'CHILDREN')

        rack_node = None
        for child in wc_children.findall('NODE'):
            name_text = child.findtext('NAME', '').strip()
            type_text = child.findtext('TYPE', '').strip()
            if name_text == 'Rack' and type_text == '4':
                rack_node = child
                break
        if rack_node is None:
            rack_node = ET.Element('NODE')
            ET.SubElement(rack_node, 'X').text = '0'
            ET.SubElement(rack_node, 'Y').text = '0'
            ET.SubElement(rack_node, 'TYPE').text = '4'
            ET.SubElement(rack_node, 'NAME', {'translate': 'true'}).text = 'Rack'
            ET.SubElement(rack_node, 'SX').text = '1'
            ET.SubElement(rack_node, 'SY').text = '1'
            ET.SubElement(rack_node, 'W').text = '0'
            ET.SubElement(rack_node, 'H').text = '0'
            ET.SubElement(rack_node, 'D').text = '0'
            ET.SubElement(rack_node, 'PATH', {'isanim': 'false'}).text = '../art/Background/grid_100x100.png'
            ET.SubElement(rack_node, 'CHILDREN')
            ET.SubElement(rack_node, 'MANUAL_SCALING').text = 'false'
            ET.SubElement(rack_node, 'SCALED_PIXMAP_WIDTH').text = '0'
            ET.SubElement(rack_node, 'SCALED_PIXMAP_HEIGHT').text = '0'
            ET.SubElement(rack_node, 'INIT_WIDTH').text = '0'
            ET.SubElement(rack_node, 'INIT_HEIGHT').text = '0'
            ET.SubElement(rack_node, 'INIT_DEPTH').text = '0'
            ET.SubElement(rack_node, 'INIT_SX').text = '1'
            ET.SubElement(rack_node, 'INIT_SY').text = '1'
            ET.SubElement(rack_node, 'INIT_SZ').text = '1'
            ET.SubElement(rack_node, 'BG_TILED').text = 'false'
            ET.SubElement(rack_node, 'CUSTOM_IMAGE_WIDTH').text = '-1'
            ET.SubElement(rack_node, 'CUSTOM_IMAGE_HEIGHT').text = '-1'
            ET.SubElement(rack_node, 'SCALE_FACTOR').text = '1'
            ET.SubElement(rack_node, 'UUID_STR').text = f'{{{rack_uuid}}}'
            ET.SubElement(rack_node, 'SLOT').text = '0'
            ET.SubElement(rack_node, 'SUB_SLOT').text = '0'
            wc_children.append(rack_node)

        rack_children = rack_node.find('CHILDREN')
        if rack_children is None:
            rack_children = ET.SubElement(rack_node, 'CHILDREN')
        for node in list(rack_children.findall('NODE')):
            rack_children.remove(node)

        pdu_node = ET.Element('NODE')
        ET.SubElement(pdu_node, 'X').text = '0'
        ET.SubElement(pdu_node, 'Y').text = '0'
        ET.SubElement(pdu_node, 'TYPE').text = '6'
        ET.SubElement(pdu_node, 'NAME', {'translate': 'true'}).text = 'Power Distribution Device0'
        ET.SubElement(pdu_node, 'SX').text = '0.2'
        ET.SubElement(pdu_node, 'SY').text = '0.2'
        ET.SubElement(pdu_node, 'W').text = '20'
        ET.SubElement(pdu_node, 'H').text = '20'
        ET.SubElement(pdu_node, 'D').text = '0'
        ET.SubElement(pdu_node, 'PATH', {'isanim': 'false'}).text = '../art/Background/grid_100x100.png'
        ET.SubElement(pdu_node, 'CHILDREN')
        ET.SubElement(pdu_node, 'MANUAL_SCALING').text = 'false'
        ET.SubElement(pdu_node, 'SCALED_PIXMAP_WIDTH').text = '0'
        ET.SubElement(pdu_node, 'SCALED_PIXMAP_HEIGHT').text = '0'
        ET.SubElement(pdu_node, 'INIT_WIDTH').text = '20'
        ET.SubElement(pdu_node, 'INIT_HEIGHT').text = '20'
        ET.SubElement(pdu_node, 'INIT_DEPTH').text = '0'
        ET.SubElement(pdu_node, 'INIT_SX').text = '0.2'
        ET.SubElement(pdu_node, 'INIT_SY').text = '0.2'
        ET.SubElement(pdu_node, 'INIT_SZ').text = '0.2'
        ET.SubElement(pdu_node, 'BG_TILED').text = 'false'
        ET.SubElement(pdu_node, 'CUSTOM_IMAGE_WIDTH').text = '-1'
        ET.SubElement(pdu_node, 'CUSTOM_IMAGE_HEIGHT').text = '-1'
        ET.SubElement(pdu_node, 'SCALE_FACTOR').text = '1'
        ET.SubElement(pdu_node, 'UUID_STR').text = f'{{{uuid.uuid4()}}}'
        ET.SubElement(pdu_node, 'SLOT').text = '0'
        ET.SubElement(pdu_node, 'SUB_SLOT').text = '0'
        rack_children.append(pdu_node)

        corp_children = corporate_office.find('CHILDREN')
        if corp_children is None:
            corp_children = ET.SubElement(corporate_office, 'CHILDREN')
        for node in list(corp_children.findall('NODE')):
            if node.findtext('TYPE', '').strip() == '6':
                corp_children.remove(node)

        for device in devices_elem.findall('DEVICE'):
            workspace = device.find('WORKSPACE')
            if workspace is None:
                continue
            engine = device.find('ENGINE')
            if engine is None:
                continue
            name_elem = engine.find('NAME')
            device_name = name_elem.text if name_elem is not None else 'Device'
            device_type = engine.findtext('TYPE', '')
            physical = workspace.find('PHYSICAL')
            physical_cpur = workspace.find('PHYSICAL_CPUR')
            if physical is None or physical_cpur is None or not physical.text:
                continue
            uuid_parts = [part.strip() for part in physical.text.split(',') if part.strip()]
            if not uuid_parts:
                continue
            device_uuid = uuid_parts[-1]
            x_val = physical_cpur.findtext('X', '0')
            y_val = physical_cpur.findtext('Y', '0')
            slot_val = physical_cpur.findtext('SLOT', '0')
            subslot_val = physical_cpur.findtext('SUBSLOT', '0')
            node = self._build_device_node(device_name, x_val, y_val, slot_val, subslot_val, device_uuid)
            if node is None:
                continue
            lowered = device_type.lower()
            if 'pc' in lowered or 'server' in lowered:
                corp_children.append(node)
            else:
                rack_children.append(node)

    def _inject_instruction_note(self, root):
        if not self._instruction_note_text and not self._site_labels:
            return
        physicalworkspace = root.find('PHYSICALWORKSPACE')
        if physicalworkspace is None:
            return
        notes_elem = physicalworkspace.find('NOTES')
        if notes_elem is None:
            notes_elem = ET.SubElement(physicalworkspace, 'NOTES')
        else:
            for existing in list(notes_elem.findall('NOTE')):
                notes_elem.remove(existing)
        if self._instruction_note_text:
            note_elem = ET.SubElement(notes_elem, 'NOTE', {'uuid': f'{{{uuid.uuid4()}}}'})
            x_val, y_val = self._note_position
            ET.SubElement(note_elem, 'X').text = str(x_val)
            ET.SubElement(note_elem, 'Y').text = str(y_val)
            ET.SubElement(note_elem, 'Z').text = '40000'
            ET.SubElement(note_elem, 'TEXT', {'translate': 'true'}).text = self._instruction_note_text
            ET.SubElement(note_elem, 'NOTECLUSTERID').text = '1-1'
            ET.SubElement(note_elem, 'MEM_ADDR').text = str(self._note_mem_seed)
            self._note_mem_seed += 256

        for label in self._site_labels:
            label_elem = ET.SubElement(notes_elem, 'NOTE', {'uuid': f'{{{uuid.uuid4()}}}'})
            x_val, y_val = label['position']
            ET.SubElement(label_elem, 'X').text = str(x_val)
            ET.SubElement(label_elem, 'Y').text = str(y_val)
            ET.SubElement(label_elem, 'Z').text = str(label.get('z', 40000))
            ET.SubElement(label_elem, 'TEXT', {'translate': 'true'}).text = label['text']
            cluster_id = label.get('cluster_id')
            ET.SubElement(label_elem, 'NOTECLUSTERID').text = cluster_id or ''
            ET.SubElement(label_elem, 'MEM_ADDR').text = str(self._note_mem_seed)
            self._note_mem_seed += 256

    def _find_node_by_name_and_type(self, node, target_name, target_type):
        if node is None:
            return None
        name_elem = node.find('NAME')
        type_elem = node.find('TYPE')
        if name_elem is not None and type_elem is not None:
            if (name_elem.text or '').strip() == target_name and (type_elem.text or '').strip() == target_type:
                return node
        for child in node.findall('NODE'):
            result = self._find_node_by_name_and_type(child, target_name, target_type)
            if result is not None:
                return result
        children = node.find('CHILDREN')
        if children is not None:
            for child in children.findall('NODE'):
                result = self._find_node_by_name_and_type(child, target_name, target_type)
                if result is not None:
                    return result
        return None

    def _build_device_node(self, name, x_val, y_val, slot_val, subslot_val, uuid_str):
        uuid_clean = uuid_str if uuid_str.startswith('{') else f'{{{uuid_str}}}'
        node = ET.Element('NODE')
        ET.SubElement(node, 'X').text = str(x_val)
        ET.SubElement(node, 'Y').text = str(y_val)
        ET.SubElement(node, 'TYPE').text = '6'
        ET.SubElement(node, 'NAME', {'translate': 'true'}).text = name
        ET.SubElement(node, 'SX').text = '1'
        ET.SubElement(node, 'SY').text = '1'
        ET.SubElement(node, 'W').text = '0'
        ET.SubElement(node, 'H').text = '0'
        ET.SubElement(node, 'D').text = '0'
        ET.SubElement(node, 'PATH', {'isanim': 'false'}).text = '../art/Background/grid_100x100.png'
        ET.SubElement(node, 'CHILDREN')
        ET.SubElement(node, 'MANUAL_SCALING').text = 'false'
        ET.SubElement(node, 'SCALED_PIXMAP_WIDTH').text = '0'
        ET.SubElement(node, 'SCALED_PIXMAP_HEIGHT').text = '0'
        ET.SubElement(node, 'INIT_WIDTH').text = '0'
        ET.SubElement(node, 'INIT_HEIGHT').text = '0'
        ET.SubElement(node, 'INIT_DEPTH').text = '0'
        ET.SubElement(node, 'INIT_SX').text = '1'
        ET.SubElement(node, 'INIT_SY').text = '1'
        ET.SubElement(node, 'INIT_SZ').text = '1'
        ET.SubElement(node, 'BG_TILED').text = 'false'
        ET.SubElement(node, 'CUSTOM_IMAGE_WIDTH').text = '-1'
        ET.SubElement(node, 'CUSTOM_IMAGE_HEIGHT').text = '-1'
        ET.SubElement(node, 'SCALE_FACTOR').text = '1'
        ET.SubElement(node, 'UUID_STR').text = uuid_clean
        ET.SubElement(node, 'SLOT').text = str(slot_val)
        ET.SubElement(node, 'SUB_SLOT').text = str(subslot_val)
        return node

    def _extract_save_ref(self, device_elem):
        engine = device_elem.find('ENGINE')
        if engine is None:
            raise ValueError('Device template missing ENGINE block')
        save_ref = engine.find('SAVE_REF_ID')
        if save_ref is None or not save_ref.text:
            raise ValueError('Device template missing SAVE_REF_ID; test.xml must include one')
        return save_ref.text

    def _deep_copy_element(self, elem):
        new_elem = ET.Element(elem.tag, elem.attrib)
        new_elem.text = elem.text
        new_elem.tail = elem.tail
        for child in elem:
            new_elem.append(self._deep_copy_element(child))
        return new_elem

    def _apply_profile(self, device_elem, dev_info):
        profile_spec = dev_info.get('profile')
        if not profile_spec:
            return
        profile_names = profile_spec if isinstance(profile_spec, (list, tuple)) else [profile_spec]

        profiles = []
        for profile_name in profile_names:
            profile = PROFILE_LIBRARY.get(profile_name)
            if profile is None:
                raise ValueError(f'Profile {profile_name} is not defined')
            expected = profile.get('device_type')
            if expected and not dev_info['type'].lower().startswith(expected):
                raise ValueError(f'Profile {profile_name} expects device type {expected}')
            profiles.append(profile)

        engine = device_elem.find('ENGINE')
        if engine is None:
            return

        running_blocks = [profile.get('running_config') for profile in profiles if profile.get('running_config')]
        startup_blocks = [profile.get('startup_config') for profile in profiles if profile.get('startup_config')]

        if running_blocks:
            merged_running = '\n'.join(block.strip('\n') for block in running_blocks)
            self._write_config_section(engine, 'RUNNINGCONFIG', merged_running)
        if startup_blocks:
            merged_startup = '\n'.join(block.strip('\n') for block in startup_blocks)
            self._write_config_section(engine, 'STARTUPCONFIG', merged_startup)

    def _write_config_section(self, engine_elem, section_name, config_text):
        section = engine_elem.find(section_name)
        if section is None:
            section = ET.SubElement(engine_elem, section_name)
        section.clear()
        for line in config_text.strip('\n').splitlines():
            line_elem = ET.SubElement(section, 'LINE')
            line_elem.text = line
