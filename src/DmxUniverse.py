from DmxDevice import Device
import pyenttec as dmx
from dslink.Value import Value
from Utils import *


class Universe:
    def __init__(self, dslink, node):
        self.dslink = dslink
        self.node = node
        self.serial_port = self.node.get_attribute("@SerialPort")
        self.devices = {}
        self.connection = None
        self.statnode = self.node.get("/Status")
        if self.statnode is None:
            self.statnode = self.node.create_child("Status")
        self.statnode.set_type("string")
        self.statnode.set_value("Setting up connection")

        self.dslink.multiverse[node.name] = self
        self.start()

    def restore_devices(self):
        for child_name in self.node.children.copy():
            if child_name == "Status":
                continue
            child = self.node.get("/%s" % child_name)
            if child is not None:
                if node_has_attribute(child, "@BaseAddress") and node_has_attribute(child, "@ChannelCount"):
                    dev = Device(self, child)
                    dev.restore_last()
                    continue
                else:
                    invok = child.get_config("$invokable")
                    if invok is not None and (invok == "read" or invok == "write" or invok == "config"):
                        continue
            self.node.remove_child(child_name)

    def start(self):
        try:
            self.connection = dmx.DMXConnection(com_port=self.serial_port)
        except dmx.EnttecPortOpenError:
            self.connection = None

        if self.connection is not None:
            self.statnode.set_value("Connected")

            for device in self.devices.values():
                device.send_local_values()

        else:
            self.statnode.set_value("Failed to connect")

        self.setup_actions()

    def stop(self):
        if self.connection is not None:
            self.connection.close()
            self.connection = None
            self.statnode.set_value("Stopped")

    def update_edit_action(self, port_list):
        edit_univ = self.node.get("/edit")
        if edit_univ is not None:
            edit_univ.set_parameters(self.get_edit_action_params(port_list))

    def get_edit_action_params(self, port_list):
        if self.serial_port not in port_list:
            port_list.append(self.serial_port)

        params = [
            {
                "name": "Serial Port",
                "type": Value.build_enum(port_list),
                "default": self.serial_port
            },
            {
                "name": "Serial Port (manual entry)",
                "type": "string"
            }
        ]

        return params

    def setup_actions(self):
        serports = serial_ports()
        params = self.get_edit_action_params(serports)

        edit_univ = self.node.get("/edit")
        if edit_univ is None:
            edit_univ = self.node.create_child("edit")
            edit_univ.set_parameters(params)
            edit_univ.set_profile("edit_universe")
            edit_univ.set_invokable("config")
            edit_univ.set_display_name("Edit")
            edit_univ.set_transient(True)
        else:
            edit_univ.set_parameters(params)

        if self.node.get("/remove") is None:
            remove_univ = self.node.create_child("remove")
            remove_univ.set_profile("remove_universe")
            remove_univ.set_invokable("config")
            remove_univ.set_display_name("Remove")
            remove_univ.set_transient(True)

        self.make_add_device_action()

        if self.node.get("/control_channel") is None:
            control_channel = self.node.create_child("control_channel")
            control_channel.set_parameters([
                {
                    "name": "Channel",
                    "type": "number",
                },
                {
                    "name": "Value",
                    "type": "number"
                }
            ])
            control_channel.set_profile("control_channel")
            control_channel.set_invokable("config")
            control_channel.set_display_name("Control Channel")
            control_channel.set_transient(True)

        if self.node.get("/all_channels") is None:
            all_channels = self.node.create_child("all_channels")
            all_channels.set_columns([
                {
                    "name": "Value",
                    "type": "number"
                }
            ])
            all_channels.set_config("$result", "table")
            all_channels.set_profile("all_channels")
            all_channels.set_invokable("config")
            all_channels.set_display_name("All Channels")
            all_channels.set_transient(True)

    def make_add_device_action(self):

        # devlst = []
        # for dev_id, device in self.dslink.ola_device_list.items():
        #     name = device.name + " - " + dev_id
        #     if name not in self.devices:
        #         devlst.append(name)

        if self.node.get("/add_device") is None:
            add_dev = self.node.create_child("add_device")
            add_dev.set_parameters([
                {
                    "name": "Name",
                    "type": "string"
                },
                {
                    "name": "Base Address",
                    "type": "number"
                },
                {
                    "name": "Number of Channels",
                    "type": "number"
                }
            ])
            add_dev.set_profile("add_device")
            add_dev.set_invokable("config")
            add_dev.set_display_name("Add Device")
            add_dev.set_transient(True)

    def update_devices(self):
        for device in self.devices.values():
            device.update()

    # Actions

    def edit(self, params):
        ser_port = params["Serial Port"]
        if "Serial Port (manual entry)" in params:
            ser_port_man = params["Serial Port (manual entry)"]
            if ser_port_man is not None and len(ser_port_man) > 0:
                ser_port = ser_port_man
        self.serial_port = ser_port
        self.node.set_attribute("@SerialPort", self.serial_port)
        self.stop()
        self.start()

    def remove(self):
        self.stop()
        self.dslink.multiverse.pop(self.node.name)
        self.node.parent.remove_child(self.node.name)

    def add_device(self, params):
        name = params["Name"]
        base_addr = int(params["Base Address"])
        chan_count = int(params["Number of Channels"])

        if base_addr + chan_count > 512 or base_addr < 0 or chan_count < 1:
            return

        if self.node.get("/%s" % name) is None:

            dev_node = self.node.create_child(name)
            dev_node.set_attribute("@BaseAddress", base_addr)
            dev_node.set_attribute("@ChannelCount", chan_count)
            dev = Device(self, dev_node)
            dev.start()

    def control_channel(self, params):
        channel_num = int(params["Channel"])
        value = int(params["Value"])

        if self.connection is None:
            return

        if channel_num < 0 or channel_num >= 512 or value < 0 or value > 255:
            return

        self.connection.set_channel(channel_num, value)
        self.connection.render()
        self.update_devices()

    def all_channels(self):
        if self.connection is None:
            return [
                [
                ]
            ]
        table = []
        for i in range(512):
            table.append([self.connection.dmx_frame[i]])
        return table
