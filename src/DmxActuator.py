import ast
from dslink import Value


class Actuator:
    def __init__(self, device, node):
        self.device = device
        self.node = node
        self.node.set_writable("write")
        self.node.set_value_callback = self.set_value

        self.device.actuators[self.node.name] = self

    def start(self):
        self.make_edit_action()
        self.make_remove_action()

    def make_edit_action(self):
        params = self.get_edit_params()
        edit_act = self.node.get("/edit")
        if edit_act is None:
            edit_act = self.node.create_child("edit")
            edit_act.set_parameters(params)
            edit_act.set_profile("edit_actuator")
            edit_act.set_invokable("config")
            edit_act.set_display_name("Edit")
            edit_act.set_transient(True)
        else:
            edit_act.set_parameters(params)

    def make_remove_action(self):
        rem_act = self.node.get("/remove")
        if rem_act is None:
            rem_act = self.node.create_child("remove")
            rem_act.set_profile("remove_actuator")
            rem_act.set_invokable("config")
            rem_act.set_display_name("Remove")
            rem_act.set_transient(True)

    def get_edit_params(self):
        return []

    def set_value(self, node, value):
        return

    def edit(self, params):
        return

    def remove(self):
        self.device.actuators.pop(self.node.name)
        self.node.parent.remove_child(self.node.name)

    def update(self):
        return


class LinearActuator(Actuator):
    def __init__(self, device, node):
        Actuator.__init__(self, device, node)
        self.channel = self.node.get_attribute("@Channel")
        self.node.set_type("number")

    def get_edit_params(self):
        return [
                {
                    "name": "Channel",
                    "type": "number",
                    "default": self.channel
                }
            ]

    def set_value(self, node, value):
        if value is None:
            return
        self.device.set_channel_value(self.channel, value)
        self.device.publish_updates()

    def edit(self, params):
        chan = int(params["Channel"])
        self.channel = chan
        self.node.set_attribute("@Channel", self.channel)
        self.start()

    def update(self):
        self.node.set_value(self.device.channel_values[self.channel])


class RgbActuator(Actuator):
    def __init__(self, device, node):
        Actuator.__init__(self, device, node)
        self.red = self.node.get_attribute("@RedChannel")
        self.green = self.node.get_attribute("@GreenChannel")
        self.blue = self.node.get_attribute("@BlueChannel")
        self.node.set_type("string")
        self.node.set_config("$editor", "color")

    def get_edit_params(self):
        return [
            {
                "name": "Red Channel",
                "type": "number",
                "default": self.red
            },
            {
                "name": "Green Channel",
                "type": "number",
                "default": self.green
            },
            {
                "name": "Blue Channel",
                "type": "number",
                "default": self.blue
            }
        ]

    def set_value(self, node, value):
        if value is None:
            return
        num = int(value)
        r = (num >> 16) & 0xff
        g = (num >> 8) & 0xff
        b = num & 0xff
        self.device.set_channel_value(self.red, r)
        self.device.set_channel_value(self.green, g)
        self.device.set_channel_value(self.blue, b)
        self.device.publish_updates()

    def edit(self, params):
        self.red = int(params["Red Channel"])
        self.green = int(params["Green Channel"])
        self.blue = int(params["Blue Channel"])
        self.node.set_attribute("@RedChannel", self.red)
        self.node.set_attribute("@GreenChannel", self.green)
        self.node.set_attribute("@BlueChannel", self.blue)
        self.start()

    def update(self):
        r = self.device.channel_values[self.red]
        g = self.device.channel_values[self.green]
        b = self.device.channel_values[self.blue]
        self.node.set_value("#%x%x%x" % (r, g, b))


class MultistateActuator(Actuator):
    def __init__(self, device, node):
        Actuator.__init__(self, device, node)
        self.channel = self.node.get_attribute("@Channel")
        self.mappings = ast.literal_eval(self.node.get_attribute("@Mappings"))
        self.node.set_type(Value.build_enum(self.mappings.keys()))

    def get_edit_params(self):
        return [
            {
                "name": "Channel",
                "type": "number",
                "default": self.channel
            },
            {
                "name": "Value Mappings",
                "type": "string",
                "default": str(self.mappings)
            }
        ]

    def set_value(self, node, value):
        if value is None:
            return
        self.device.set_channel_value(self.channel, self.mappings[value][0])
        self.device.publish_updates()

    def edit(self, params):
        self.channel = int(params["Channel"])
        self.mappings = ast.literal_eval(params["Value Mappings"])

        self.node.set_attribute("@Channel", self.channel)
        self.node.set_attribute("@Mappings", str(self.mappings))
        self.start()

    def update(self):
        num = self.device.channel_values[self.channel]
        for name, numrange in self.mappings.items():
            if numrange[0] <= num <= numrange[1]:
                self.node.set_value(name)
                return
