from DmxActuator import LinearActuator, RgbActuator, MultistateActuator
from Utils import *


class Device:
    def __init__(self, universe, node):
        self.universe = universe
        self.node = node
        self.base_address = self.node.get_attribute("@BaseAddress")
        self.channel_count = self.node.get_attribute("@ChannelCount")
        self.channel_values = [0] * self.channel_count
        self.actuators_node = self.node.get("/actuators")
        if self.actuators_node is None:
            self.actuators_node = self.node.create_child("actuators")
        self.actuators = {}

        self.universe.devices[self.node.name] = self

    def restore_last(self):
        for child_name in self.node.children.copy():
            if child_name == "actuators":
                continue
            if child_name.startswith("channel_"):
                index_str = child_name.replace("channel_", "")
                if index_str.isdigit() and int(index_str) < self.channel_count:
                    index = int(index_str)
                    child = self.node.get("/%s" % child_name)
                    if child is not None and child.get_value() is not None:
                        self.channel_values[index] = child.get_value()
                    continue
            self.node.remove_child(child_name)

        self.send_local_values()
        self.start()

        self.restore_actuators()

    def send_local_values(self):
        if self.universe.connection is not None:
            for i in range(self.channel_count):
                val = self.channel_values[i]
                channel_num = self.base_address + i
                if 0 <= val <= 255 and 0 <= channel_num < 512:
                    self.universe.connection.set_channel(channel_num, val)

            self.universe.connection.render()
            self.universe.update_devices()

    def restore_actuators(self):
        for child_name in self.actuators_node.children.copy():
            child = self.actuators_node.get("/%s" % child_name)
            if child is not None:
                if node_has_attribute(child, "@Channel"):
                    if node_has_attribute(child, "@Mappings"):
                        ma = MultistateActuator(self, child)
                        ma.start()
                    else:
                        la = LinearActuator(self, child)
                        la.start()
                elif node_has_attribute(child, "@RedChannel") and node_has_attribute(child, "@GreenChannel") and \
                        node_has_attribute(child, "@BlueChannel"):
                    ra = RgbActuator(self, child)
                    ra.start()

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

        for actuator in self.actuators.values():
            actuator.update()

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

        if self.node.get("/add_linear_actuator") is None:
            add_lin = self.node.create_child("add_linear_actuator")
            add_lin.set_parameters([
                {
                    "name": "Name",
                    "type": "string"
                },
                {
                    "name": "Channel",
                    "type": "number"
                }
            ])
            add_lin.set_profile("add_linear_actuator")
            add_lin.set_invokable("config")
            add_lin.set_display_name("Add Linear Actuator")
            add_lin.set_transient(True)

        if self.node.get("/add_rgb_actuator") is None:
            add_rgb = self.node.create_child("add_rgb_actuator")
            add_rgb.set_parameters([
                {
                    "name": "Name",
                    "type": "string"
                },
                {
                    "name": "Red Channel",
                    "type": "number"
                },
                {
                    "name": "Green Channel",
                    "type": "number"
                },
                {
                    "name": "Blue Channel",
                    "type": "number"
                }
            ])
            add_rgb.set_profile("add_rgb_actuator")
            add_rgb.set_invokable("config")
            add_rgb.set_display_name("Add RGB Actuator")
            add_rgb.set_transient(True)

        if self.node.get("/add_multistate_actuator") is None:
            add_mul = self.node.create_child("add_multistate_actuator")
            add_mul.set_parameters([
                {
                    "name": "Name",
                    "type": "string"
                },
                {
                    "name": "Channel",
                    "type": "number"
                },
                {
                    "name": "Value Mappings",
                    "type": "string",
                    "default": "{}"
                }
            ])
            add_mul.set_profile("add_multistate_actuator")
            add_mul.set_invokable("config")
            add_mul.set_display_name("Add Multistate Actuator")
            add_mul.set_transient(True)

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

    def set_channel_value(self, channel, value):
        self.channel_values[channel] = value
        self.update_channel_node(channel)
        if self.universe.connection is None:
            return
        channel_num = self.base_address + channel
        if 0 <= value <= 255 and 0 <= channel_num < 512:
            self.universe.connection.set_channel(channel_num, value)

    def publish_updates(self):
        if self.universe.connection is None:
            return
        self.universe.connection.render()
        self.universe.update_devices()

    # Actions

    def edit(self, params):
        base_addr = int(params["Base Address"])
        chan_count = int(params["Number of Channels"])
        if base_addr + chan_count > 512 or base_addr < 0 or chan_count < 1:
            return
        if chan_count < self.channel_count:
            for i in range(chan_count, self.channel_count):
                self.node.remove_child("channel_" + str(i))
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
            self.set_channel_value(i, val)
        self.publish_updates()

    def add_linear_actuator(self, params):
        name = params["Name"]
        chan = int(params["Channel"])
        if self.actuators_node.get("/%s" % name) is None:
            linact_node = self.actuators_node.create_child(name)
            linact_node.set_attribute("@Channel", chan)
            linact_node.set_type("number")
            linact_node.set_value(self.channel_values[chan])

            la = LinearActuator(self, linact_node)
            la.start()

    def add_rgb_actuator(self, params):
        name = params["Name"]
        red = int(params["Red Channel"])
        green = int(params["Green Channel"])
        blue = int(params["Blue Channel"])
        if self.actuators_node.get("/%s" % name) is None:
            rgbact_node = self.actuators_node.create_child(name)
            rgbact_node.set_attribute("@RedChannel", red)
            rgbact_node.set_attribute("@GreenChannel", green)
            rgbact_node.set_attribute("@BlueChannel", blue)
            rgbact_node.set_type("string")

            ra = RgbActuator(self, rgbact_node)
            ra.start()
            ra.update()

    def add_multistate_actuator(self, params):
        name = params["Name"]
        chan = int(params["Channel"])
        mappings = params["Value Mappings"]
        if self.actuators_node.get("/%s" % name) is None:
            mulact_node = self.actuators_node.create_child(name)
            mulact_node.set_attribute("@Channel", chan)
            mulact_node.set_attribute("@Mappings", mappings)

            ma = MultistateActuator(self, mulact_node)
            ma.start()
            ma.update()
