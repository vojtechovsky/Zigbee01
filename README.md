The Python project deals with direct communication with a zigbee gateway via a serial port.
To run, you need to install the zigpy, bellows packages and all their required dependencies, preferably in a virtual environment.
The program is based on the project
Malte Gruber: https://github.com/MalteGruber/zigpy_standalone
and discussion
https://github.com/zigpy/zigpy/issues/452
The project is executable from the windows console because it does not use a shell package.
The program is tested with Python versions 3.9 and 3.11.

Bellows package supports HW with EFR32MG21 chip (SKYCONNECT, SONOFF Dongle Plus E).
The driver for Windows is labeled Silicon Labs CP210x USB to UART Bridge (COMx).
If needed, you can download it here:
https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers?tab=downloads

In the section
app = await ControllerApplication.new(ControllerApplication.SCHEMA({
     "database_path": "myzigbee.db",
     "device": {
         "path": "COM3",
     }
}))

fix "COM3" to your Silicon Labs port.
 
Program control:
q - Quit
l - List: list of available devices
p, int - Pair: Time to pair 1 ÷ 255
d, int - device info: device number
b, int, int, int, [in / out] - Bind: Device, EndPoint, Cluster, Type
u, int, int, int, [in / out] - Unbind: Device, EndPoint, Cluster, Type
c, int, int, int, [in / out], [0 / 1] - Command for OnOff cluster
ci, int - Cluster info: cluster number

The zigpy package runs several separate threads. The program occasionally reports runtime errors that appear to be related to the time required to complete the activities of individual threads.
