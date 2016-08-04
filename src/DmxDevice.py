

class Device:
    def __init__(self, universe, node):
        self.universe = universe
        self.node = node
        self.base_address = self.node.get_attribute("@BaseAddress")
        self.channel_count = self.node.get_attribute("@ChannelCount")
        self.channel_values = [0] * self.channel_count

        self.universe.devices[self.node.name] = self

    def restore_last(self):
        for child_name in self.node.children.copy():
            if child_name.startswith("channel_"):
                index_str = child_name.replace("channel_", "")
                if index_str.isdigit():
                    index = int(index_str)
                    child = self.node.get("/%s" % child_name)
                    if child is not None and child.get_value() is not None:
                        self.channel_values[index] = child.get_value()
                    continue
            self.node.remove_child(child_name)

        if self.universe.connection is None:
            return

        for i in range(self.channel_count):
            val = self.channel_values[i]
            channel_num = self.base_address + i
            if 0 <= val <= 255 and 0 <= channel_num < 512:
                self.universe.connection.set_channel(channel_num, val)

        self.universe.connection.render()
        self.universe.update_devices()
        self.start()

    def start(self):
        self.update_channels()

        self.setup_actions()

    def update(self):
        self.update_channels()

        self.make_control_action()

    def update_channels(self):
        if self.universe.connection is not None:
            start = self.base_address
            end = start + self.channel_count
            self.channel_values = self.universe.connection.dmx_frame[start:end]

        for i in range(self.channel_count):
            self.update_channel_node(i)

    def update_channel_node(self, channel):
        name = "channel_" + str(channel)
        ch_node = self.node.get("/%s" % name)
        if ch_node is None:
            ch_node = self.node.create_child(name)
            ch_node.set_display_name("Channel " + str(channel))
            ch_node.set_type("number")
        ch_node.set_value(self.channel_values[channel])

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
            edit_dev.set_transient(True)
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
            remove_dev.set_transient(True)

        self.make_control_action()

    def make_control_action(self):
        paramlist = [
            {
                "name": "Channel " + str(i),
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
            control_channels.set_transient(True)
        else:
            control_channels.set_parameters(paramlist)

    # Actions

    def edit(self, params):
        base_addr = int(params["Base Address"])
        chan_count = int(params["Number of Channels"])
        if base_addr + chan_count > 512 or base_addr < 0 or chan_count < 1:
            return
        self.base_address = base_addr
        self.channel_count = chan_count
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
            val = int(params["Channel " + str(i)])
            channel_num = self.base_address + i
            if 0 <= val <= 255 and 0 <= channel_num < 512:
                self.universe.connection.set_channel(channel_num, val)
        self.universe.connection.render()
        self.universe.update_devices()
