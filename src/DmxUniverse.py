from DmxDevice import Device
import pysimpledmx
from dslink.Node import Node


class Universe:
    def __init__(self, dslink, node):
        self.dslink = dslink
        self.node = node
        self.serial_port = self.node.get_attribute("@SerialPort")
        self.devices = {}
        self.connection = None
        self.statnode = self.node.create_child("Status")
        self.statnode.set_type("string")
        self.statnode.set_value("Setting up connection")

        self.dslink.multiverse[node.name] = self
        self.start()

    def start(self):
        try:
            self.connection = pysimpledmx.DMXConnection(comport=self.serial_port)
        except SystemExit:
            self.connection = None

        if self.connection is not None:
            self.statnode.set_value("Connected")
        else:
            self.statnode.set_value("Failed to connect")

        self.setup_actions()

    def stop(self):
        if self.connection is not None:
            self.connection.close()
            self.connection = None
            self.statnode.set_value("Stopped")

    def setup_actions(self):
        edit_univ = self.node.get("/edit")
        if edit_univ is None:
            edit_univ = self.node.create_child("edit")
            edit_univ.set_parameters([
                {
                    "name": "Serial Port",
                    "type": "string",
                    "default": self.serial_port
                }
            ])
            edit_univ.set_profile("edit_universe")
            edit_univ.set_invokable("config")
            edit_univ.set_display_name("Edit")
        else:
            edit_univ.set_parameters([
                {
                    "name": "Serial Port",
                    "type": "string",
                    "default": self.serial_port
                }
            ])

        if self.node.get("/remove") is None:
            remove_univ = self.node.create_child("remove")
            remove_univ.set_profile("remove_universe")
            remove_univ.set_invokable("config")
            remove_univ.set_display_name("Remove")

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

        if self.node.get("/all_channels") is None:
            all_channels = self.node.create_child("all_channels")
            all_channels.set_columns([
                {
                    "name": "Channel",
                    "type": "number"
                },
                {
                    "name": "Value",
                    "type": "number"
                }
            ])
            all_channels.set_config("$result", "table")
            all_channels.set_profile("all_channels")
            all_channels.set_invokable("config")
            all_channels.set_display_name("All Channels")

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

    def update_devices(self):
        for device in self.devices.values():
            device.update()

    # Actions

    def edit(self, params):
        self.serial_port = int(params["Serial Port"])
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

        if self.node.get("/%s" % name) is None:

            dev_node = self.node.create_child(name)
            dev_node.set_attribute("@BaseAddress", base_addr)
            dev_node.set_attribute("@ChannelCount", chan_count)
            Device(self, dev_node)

    def control_channel(self, params):
        channel_num = int(params["Channel"])
        value = int(params["Value"])

        if self.connection is None:
            return

        self.connection.setChannel(channel_num, value)
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
            table.append([i+1, self.connection.dmx_frame[i]])
        return table


