# DMX-512 DSLink
This is a DSLink for the DMX-512 protocol.

## Usage

A universe is a collection of 512 1-byte DMX channels, accessible through a serial port. From a universe's node, you can view all its channel values, set a channel value, or add a device.  
A device (in this DSLink) is a group of consecutive channels, specified by a base address and number of channels. A device node displays the values of all of its channels as metrics.

Actuators can be added to a device for more straightforward control. Linear actuators (e.g. dimmers, pan, tilt, etc.) consist of one channel. RGB actuators take 3 channels (red, green, and blue) and allow setting a value using a color picker. Multistate actuators use one channel, and use a map of names to numerical ranges to specify the possible states. 
E.g. "{'Open': [0, 35], 'Red': [36, 70], 'Cyan': [71, 105], 'Green': [106, 140], 'Yellow': [141, 175], 'Blue': [176, 210], 'Magenta': [211, 255]}"
