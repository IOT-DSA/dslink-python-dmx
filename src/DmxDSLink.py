import dslink
from dslink.Value import Value
from DmxUniverse import Universe
from Utils import *


class DmxDSLink(dslink.DSLink):
    def start(self):
        self.multiverse = {}
        # self.ola_device_list = {}
        # self.wrapper = ClientWrapper()
        # self.wrapper.Run()

        # self.scan_for_devices()

        self.responder.profile_manager.create_profile("add_universe")
        self.responder.profile_manager.register_callback("add_universe", self.add_universe)

        self.responder.profile_manager.create_profile("scan_for_ports")
        self.responder.profile_manager.register_callback("scan_for_ports", self.scan_for_ports)

        self.responder.profile_manager.create_profile("edit_universe")
        self.responder.profile_manager.register_callback("edit_universe", self.edit_universe)

        self.responder.profile_manager.create_profile("remove_universe")
        self.responder.profile_manager.register_callback("remove_universe", self.remove_universe)

        self.responder.profile_manager.create_profile("add_device")
        self.responder.profile_manager.register_callback("add_device", self.add_device)

        self.responder.profile_manager.create_profile("control_channel")
        self.responder.profile_manager.register_callback("control_channel", self.control_channel)

        self.responder.profile_manager.create_profile("all_channels")
        self.responder.profile_manager.register_callback("all_channels", self.all_channels)

        self.responder.profile_manager.create_profile("edit_device")
        self.responder.profile_manager.register_callback("edit_device", self.edit_device)

        self.responder.profile_manager.create_profile("remove_device")
        self.responder.profile_manager.register_callback("remove_device", self.remove_device)

        self.responder.profile_manager.create_profile("control_device_channels")
        self.responder.profile_manager.register_callback("control_device_channels", self.control_device_channels)

        self.responder.profile_manager.create_profile("add_linear_actuator")
        self.responder.profile_manager.register_callback("add_linear_actuator", self.add_linear_actuator)

        self.responder.profile_manager.create_profile("add_rgb_actuator")
        self.responder.profile_manager.register_callback("add_rgb_actuator", self.add_rgb_actuator)

        self.responder.profile_manager.create_profile("add_multistate_actuator")
        self.responder.profile_manager.register_callback("add_multistate_actuator", self.add_multistate_actuator)

        self.responder.profile_manager.create_profile("edit_actuator")
        self.responder.profile_manager.register_callback("edit_actuator", self.edit_actuator)

        self.responder.profile_manager.create_profile("remove_actuator")
        self.responder.profile_manager.register_callback("remove_actuator", self.remove_actuator)

        self.restore_last()

        self.make_add_universe_action(self.responder.get_super_root())
        self.make_port_scan_action(self.responder.get_super_root())

    def restore_last(self):
        root = self.responder.get_super_root()
        for child_name in root.children.copy():
            child = root.get("/%s" % child_name)
            if child is not None and node_has_attribute(child, "@SerialPort"):
                univ = Universe(self, child)
                univ.restore_devices()
            elif child_name != "defs":
                root.remove_child(child_name)

    def get_default_nodes(self, super_root):

        # self.make_add_universe_action(super_root)

        return super_root

    @staticmethod
    def get_add_action_params(port_list):
        params = [
            {
                "name": "Name",
                "type": "string"
            }
        ]
        if len(port_list) > 0:
            params.append({
                "name": "Serial Port",
                "type": Value.build_enum(port_list)
            })
            params.append({
                "name": "Serial Port (manual entry)",
                "type": "string"
            })
        else:
            params.append({
                "name": "Serial Port",
                "type": "string"
            })

        return params

    def make_add_universe_action(self, super_root):
        serports = serial_ports()
        params = self.get_add_action_params(serports)

        add_univ = super_root.create_child("add_universe")
        add_univ.set_parameters(params)
        add_univ.set_profile("add_universe")
        add_univ.set_invokable("config")
        add_univ.set_display_name("Add Universe")
        add_univ.set_transient(True)

    @staticmethod
    def make_port_scan_action(super_root):
        scan_ports = super_root.create_child("scan_for_ports")
        scan_ports.set_profile("scan_for_ports")
        scan_ports.set_invokable("config")
        scan_ports.set_display_name("Scan for serial ports")
        scan_ports.set_transient(True)

    # def got_devices(self, state, device_list):
    #     for device in device_list:
    #         self.ola_device_list[device.id] = device
    #
    # def scan_for_devices(self):
    #     self.wrapper.Client().FetchDevices(self.got_devices)

    # ----------------------------------------------------------------------
    # Actions
    # ----------------------------------------------------------------------

    # Top Level

    def add_universe(self, parameters):
        name = parameters[1]["Name"]
        ser_port = parameters[1]["Serial Port"]
        if "Serial Port (manual entry)" in parameters[1]:
            ser_port_man = parameters[1]["Serial Port (manual entry)"]
            if ser_port_man is not None and len(ser_port_man) > 0:
                ser_port = ser_port_man

        if self.responder.get_super_root().get("/%s" % name) is None:
            univ_node = self.responder.get_super_root().create_child(name)
            univ_node.set_attribute("@SerialPort", ser_port)
            Universe(self, univ_node)

        return [
            [
            ]
        ]

    def scan_for_ports(self, parameters):
        serports = serial_ports()

        add_univ = self.responder.get_super_root().get("/add_universe")
        if add_univ is not None:
            add_univ.set_parameters(self.get_add_action_params(serports))
        for universe in self.multiverse.values():
            universe.update_edit_action(serports)

    # Universe Level

    def edit_universe(self, parameters):
        univ_node = parameters[0].parent
        universe = self.multiverse[univ_node.name]
        universe.edit(parameters[1])
        return [
            [
            ]
        ]

    def remove_universe(self, parameters):
        univ_node = parameters[0].parent
        universe = self.multiverse[univ_node.name]
        universe.remove()
        return [
            [
            ]
        ]

    def add_device(self, parameters):
        univ_node = parameters[0].parent
        universe = self.multiverse[univ_node.name]
        universe.add_device(parameters[1])
        return [
            [
            ]
        ]

    def control_channel(self, parameters):
        univ_node = parameters[0].parent
        universe = self.multiverse[univ_node.name]
        universe.control_channel(parameters[1])
        return [
            [
            ]
        ]

    def all_channels(self, parameters):
        univ_node = parameters[0].parent
        universe = self.multiverse[univ_node.name]
        return universe.all_channels()

    # Device Level

    def edit_device(self, parameters):
        dev_node = parameters[0].parent
        univ_node = dev_node.parent
        universe = self.multiverse[univ_node.name]
        device = universe.devices[dev_node.name]
        device.edit(parameters[1])
        return [
            [
            ]
        ]

    def remove_device(self, parameters):
        dev_node = parameters[0].parent
        univ_node = dev_node.parent
        universe = self.multiverse[univ_node.name]
        device = universe.devices[dev_node.name]
        device.remove()
        return [
            [
            ]
        ]

    def control_device_channels(self, parameters):
        dev_node = parameters[0].parent
        univ_node = dev_node.parent
        universe = self.multiverse[univ_node.name]
        device = universe.devices[dev_node.name]
        device.control_channels(parameters[1])
        return [
            [
            ]
        ]

    def add_linear_actuator(self, parameters):
        dev_node = parameters[0].parent
        univ_node = dev_node.parent
        universe = self.multiverse[univ_node.name]
        device = universe.devices[dev_node.name]
        device.add_linear_actuator(parameters[1])
        return [
            [
            ]
        ]

    def add_rgb_actuator(self, parameters):
        dev_node = parameters[0].parent
        univ_node = dev_node.parent
        universe = self.multiverse[univ_node.name]
        device = universe.devices[dev_node.name]
        device.add_rgb_actuator(parameters[1])
        return [
            [
            ]
        ]

    def add_multistate_actuator(self, parameters):
        dev_node = parameters[0].parent
        univ_node = dev_node.parent
        universe = self.multiverse[univ_node.name]
        device = universe.devices[dev_node.name]
        device.add_multistate_actuator(parameters[1])
        return [
            [
            ]
        ]

    # Actuator Level

    def edit_actuator(self, parameters):
        actu_node = parameters[0].parent
        dev_node = actu_node.parent.parent
        univ_node = dev_node.parent
        universe = self.multiverse[univ_node.name]
        device = universe.devices[dev_node.name]
        actuator = device.actuators[actu_node.name]
        actuator.edit(parameters[1])
        return [
            [
            ]
        ]

    def remove_actuator(self, parameters):
        actu_node = parameters[0].parent
        dev_node = actu_node.parent.parent
        univ_node = dev_node.parent
        universe = self.multiverse[univ_node.name]
        device = universe.devices[dev_node.name]
        actuator = device.actuators[actu_node.name]
        actuator.remove()
        return [
            [
            ]
        ]

if __name__ == "__main__":
    DmxDSLink(dslink.Configuration(name="DMX512", responder=True))
