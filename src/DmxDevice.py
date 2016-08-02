
class Device:
    def __init__(self, universe, node):
        self.universe = universe
        self.node = node
        self.base_address = self.node.get_attribute("@BaseAddress")
        self.channel_count = self.node.get_attribute("@ChannelCount")
        self.channel_values = [0 for i in range(self.channel_count)]

        self.universe.devices[self.node.name] = self
        self.start()

    def start(self):
        self.update_channels()

        self.setup_actions()

    def update(self):
        self.update_channels()

        self.make_control_action()

    def update_channels(self):
        if self.universe.connection is not None:
            start = self.base_address - 1
            end = start + self.channel_count
            self.channel_values = self.universe.connection.dmx_frame[start:end]

    def setup_actions(self):
        edit_dev = self.node.get("/edit")
        if edit_dev is None:
            edit_dev = self.node.create_child("edit")
            edit_dev.set_parameters([
                {
                    "name": "Base Address",
                    "type": "number",
                    "default": self.base_address
                },
                {
                    "name": "Number of Channels",
                    "type": "number",
                    "default": self.channel_count
                }
            ])
            edit_dev.set_profile("edit_device")
            edit_dev.set_invokable("config")
            edit_dev.set_display_name("Edit")
        else:
            edit_dev.set_parameters([
                {
                    "name": "Base Address",
                    "type": "number",
                    "default": self.base_address
                },
                {
                    "name": "Number of Channels",
                    "type": "number",
                    "default": self.channel_count
                }
            ])

        if self.node.get("/remove") is None:
            remove_dev = self.node.create_child("remove")
            remove_dev.set_profile("remove_device")
            remove_dev.set_invokable("config")
            remove_dev.set_display_name("Remove")

        self.make_control_action()

    def make_control_action(self):
        paramlist = [
            {
                "name": "Channel " + i,
                "type": "number",
                "default": self.channel_values[i]
            }
            for i in range(self.channel_count)
        ]

        control_channels = self.node.get("/control_channels")
        if control_channels is None:
            control_channels = self.node.create_child("control_channels")
            control_channels.set_parameters(paramlist)
            control_channels.set_profile("control_device_channels")
            control_channels.set_invokable("config")
            control_channels.set_display_name("Control Channels")
        else:
            control_channels.set_parameters(paramlist)

    # Actions

    def edit(self, params):
        self.base_address = int(params["Base Address"])
        self.channel_count = int(params["Number of Channels"])
        self.node.set_attribute("@BaseAddress", self.base_address)
        self.node.set_attribute("@ChannelCount", self.channel_count)
        self.start()

    def remove(self):
        self.universe.devices.pop(self.node.name)
        self.node.parent.remove_child(self.node.name)

    def control_channels(self, params):
        if self.universe.connection is None:
            return
        for i in range(self.channel_count):
            val = int(params["Channel " + i])
            channel_num = self.base_address + i
            self.universe.connection.setChannel(channel_num, val)
        self.universe.connection.render()
        self.universe.update_devices()
