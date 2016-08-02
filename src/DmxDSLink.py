import dslink
from dslink.Value import Value
from DmxUniverse import Universe
import sys
import glob
import serial


class DmxDSLink(dslink.DSLink):
    def start(self):
        self.multiverse = {}
        # self.ola_device_list = {}
        # self.wrapper = ClientWrapper()
        # self.wrapper.Run()

        # self.scan_for_devices()

        self.restore_last()

        self.responder.profile_manager.create_profile("add_universe")
        self.responder.profile_manager.register_callback("add_universe", self.add_universe)

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

        self.make_add_universe_action(self.responder.get_super_root())

    def restore_last(self):
        root = self.responder.get_super_root()
        for child_name in root.children.copy():
            if child_name != "defs":
                root.remove_child(child_name)

    @staticmethod
    def serial_ports():
        """ Lists serial port names

            :raises EnvironmentError:
                On unsupported or unknown platforms
            :returns:
                A list of the serial ports available on the system
        """
        if sys.platform.startswith('win'):
            ports = ['COM%s' % (i + 1) for i in range(256)]
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            # this excludes your current terminal "/dev/tty"
            ports = glob.glob('/dev/tty[A-Za-z]*')
        elif sys.platform.startswith('darwin'):
            ports = glob.glob('/dev/tty.*')
        else:
            raise EnvironmentError('Unsupported platform')

        result = []
        for port in ports:
            try:
                s = serial.Serial(port)
                s.close()
                result.append(port)
            except (OSError, serial.SerialException):
                pass
        return result

    def get_default_nodes(self, super_root):

        # self.make_add_universe_action(super_root)

        return super_root

    def make_add_universe_action(self, super_root):

        serports = self.serial_ports()

        add_univ = super_root.create_child("add_universe")
        add_univ.set_parameters([
            {
                "name": "Name",
                "type": "string"
            },
            {
                "name": "Serial Port",
                "type": Value.build_enum(serports)
            }
        ])

        add_univ.set_profile("add_universe")
        add_univ.set_invokable("config")
        add_univ.set_display_name("Add Universe")

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
        ser_port = int(parameters[1]["Serial Port"])

        if self.responder.get_super_root().get("/%s" % name) is None:
            univ_node = self.responder.get_super_root().create_child(name)
            univ_node.set_attribute("@SerialPort", ser_port)
            Universe(self, univ_node)

        return [
            [
            ]
        ]

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
        device.contol_channels(parameters[1])
        return [
            [
            ]
        ]

if __name__ == "__main__":
    DmxDSLink(dslink.Configuration(name="DMX512", responder=True))
