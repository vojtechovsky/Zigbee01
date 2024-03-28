from zigpy.config import CONF_DEVICE
import zigpy.config as conf
from zigpy.types.named import EUI64
import zigpy.device

import asyncio
import json

# There are many different radio libraries but they all have the same API
# Replace 'bellows' with the radio that you are using, you can download it using pip.
from bellows.zigbee.application import ControllerApplication
from zigpy.zcl.clusters.general import OnOff

s=OnOff.server_commands.get(0x0)



def print_cluster_info(cluster):
    print(cluster.name)
    for x in cluster.server_commands:
        s=OnOff.server_commands.get(x)
        if s:
            print(f"Command '{s.name}', arguments= {s.schema.__dict__.get('__annotations__')}")
    for x in cluster.client_commands:
        s=OnOff.server_commands.get(x)
        if s:
            print(f"Command '{s.name}', arguments= {s.schema.__dict__.get('__annotations__')}")

    for k,v in enumerate(cluster.attributes_by_name):
        print(f"Attribute {k}: {v} ")


    

if 0:
    for c in OnOff._registry:
        cluster=OnOff._registry.get(c)
        print(cluster)
        print(cluster.attributes_by_name.keys())
        print_cluster_commands(cluster)

if 0:
    import sys
    sys.exit(1)

cluster_help="[device_id:int|ieee] [endpoint:int] [cluster:int] [in_out:str]"
cluster_template="%s %d %d %s"

def get_cluster_from_args(arg1, arg2, arg3, arg4):
    try:
        #The IEEE address is being used as keys in a dict
        device_ids=list(app.devices.keys())
        device=None
        
        try:
            dev_id=int(arg1)
            ieee=str(device_ids[dev_id])
            device=app.get_device(EUI64.convert(ieee))
        except:
            dev_help_list=[str(i)+':\t'+str(v) for i,v in enumerate(device_ids)]
            print(f"Could not find device <{dev_id}>, available devices are:")
            print("<id>\t<IEEE>")
            print('\n'.join(dev_help_list))
            print("Please provide either as a IEEE address or id")
            return None

        endpoint_id=int(arg2)
        endpoint=None
        help_list=[str(ep) for ep in device.endpoints.values()]
        try:
            endpoint=device.endpoints.get(endpoint_id)
            if not endpoint:
                raise Exception("No endpoint found")
        except:
            print(device.endpoints.values())
            
            print(f"Could not find endpoint {endpoint_id}, avalible endpoints for device {argv[1]} are:\n",'\n'.join(help_list))
            return None
        cluster_id=int(arg3)    
        out_in=arg4.lower()
        try:
            cluster=None
            if out_in in ["o","output","out"]:       
                cluster=endpoint.out_clusters.get(cluster_id)
            elif out_in in ["i","input","in"]:
                cluster=endpoint.in_clusters.get(cluster_id)
            else:
                print("Please specifiy cluster direction as i|in|input or o|out|output")
                return None
            if not cluster:
                raise Exception("Could not find cluster")
            return cluster
        except:
            print(f"Could not find cluster {cluster_id}, available clusters are:\n",'\n'.join(help_list))
        return None
    except:
        print("ERROR, Please use [device_id:int|ieee, endpoint:int, cluster:int, in_out:str]")

class MainListener:
    """
    Contains callbacks that zigpy will call whenever something happens.
    Look for `listener_event` in the Zigpy source or just look at the logged warnings.
    """

    def __init__(self, application):
        self.application = application

    def device_joined(self, device):
        print(f"Device joined: {device}")

    def attribute_updated(self, device, cluster, attribute_id, value):
        print(f"Received an attribute update {attribute_id}={value}"
              f" on cluster {cluster} from device {device}")

async def devices_list_cmd():
    print(f"Found {len(app.devices.values())} devices...")        
    for i,device in enumerate(app.devices.values()):
        print(f"{i}: {device.ieee}: '{device.manufacturer}': '{device.model}'")



async def pair_cmd(argv):
    duration=int(argv)
    await app.permit(int(duration))
    print(f"I'm waiting a maximum of {duration} seconds for pairing.")            
    await asyncio.sleep(int(duration))
    print("End of pairing.")

async def devices_cmd(argv):
    for i,device in enumerate(app.devices.values()):
        if i==int(argv):
            print(f"====== {i}: {device.manufacturer} {device.model} ====== ")
            print(f"IEEE Adress {device.ieee}")
            print(f"NWK {device.nwk}")
            print(f"Initialized {device.is_initialized}")
            print(f"rssi {device.rssi}")
            for endpoint in device.endpoints.values():

                if not isinstance(endpoint, zigpy.zdo.ZDO):
                    print(f"~~~ Endpoint #{endpoint.endpoint_id} ~~~")
                    def print_clusters_info(clusters):
                        any_clusters=False
                        for k,v in clusters.items():
                            any_clusters=True
                            #print(f"{v.cluster_id} Cluster Command: {list(command.name for command in v.client_commands.values())}")
                            print(f"\t{v.cluster_id}\t{v.ep_attribute}")
                        if not any_clusters:
                            print("\tNo clusters")
                    print("  Input clusters:")
                    print_clusters_info(endpoint.in_clusters)
                    print("  Output clusters:")
                    print_clusters_info(endpoint.out_clusters)

async def bind_cmd(a1, a2, a3, a4):
    try:
        mycluster = await get_cluster_from_args(a1, a2, a3, a4).bind()
    except:
        print("Cluster not found.")
        return
    print("Cluster connected.")
    print(mycluster)
    
async def ubind_cmd(a1, a2, a3, a4):
    try:
        mycluster = await get_cluster_from_args(a1, a2, a3, a4).unbind()
    except:
        print("Cluster not found.")
        return
    print("Cluster disconnected.")

    
async def send_cmd(a1, a2, a3, a4, a5):
    try:
        mycluster = get_cluster_from_args(a1, a2, a3, a4)
        print(mycluster)
    except:
        print("Cluster not found.")
        return
    try:
        command_id=int(a5)
    except:
        print("The command must be a number 0 or 1.")
        return
    await mycluster.command(command_id)
    print("Command sent.")
 
async def cluster_info(a1):
    mycluster=OnOff._registry.get(int(a1))
    print_cluster_info(mycluster)

async def read_user_input(arg1):
    loop = asyncio.get_running_loop()
    user_input = await loop.run_in_executor(None, input, arg1)
    return user_input

async def main():
    global app
    app = await ControllerApplication.new(ControllerApplication.SCHEMA({
        "database_path": "myzigbee.db",
        "device": {
            "path": "COM4",
        }
    }))

    listener = MainListener(app)
    app.add_listener(listener)
    app.groups.add_listener(listener)
    # await app.startup(auto_form=True)
    print("The Zigbee module core is running.")
    
    # Just run forever
    # await asyncio.get_running_loop().create_future()
    await asyncio.sleep(5)   # prostor pro vypsání zpráv spuštěných procesů
    while True:
        user_input = await read_user_input("Enter a character (q=quit, l=list, d=device, b=bind, u=unbind, p=pair, c=command, ci=cluster info): ") # asynchronous input, does not block processes

        if user_input.lower() == 'q':
            print("The program is ending.")
            break
        elif user_input.lower() == 'l':
            print("I'll start the listing procedure.")
            await devices_list_cmd()
        elif user_input.lower() == 'p':
            user_input = await read_user_input("Enter the waiting time for pairing (1 ÷ 254): ")
            print("I start the pairing process.")
            print("Activate the pairing mode of the zigbee device.")
            await pair_cmd(user_input)
        elif user_input.lower() == 'd':
            user_input = await read_user_input("Enter the device number: ") 
            await devices_cmd(user_input)  
        elif user_input.lower() == 'b':
            mydev = await read_user_input("Enter the Device number: ") 
            myepoint = await read_user_input("Enter the EndPoint number: ")
            mycluster = await read_user_input("Enter the Cluster number: ")
            myinout = await read_user_input("Enter the cluster type (in / out): ")
            await bind_cmd(mydev, myepoint, mycluster, myinout )
        elif user_input.lower() == 'u':
            mydev = await read_user_input("Enter the Device number: ") 
            myepoint = await read_user_input("Enter the EndPoint number: ")
            mycluster = await read_user_input("Enter the Cluster number: ")
            myinout = await read_user_input("Enter the cluster type (in / out): ")
            await ubind_cmd(mydev, myepoint, mycluster, myinout )    
        elif user_input.lower() == 'c':
            mydev = await read_user_input("Enter the Device number: ") 
            myepoint = await read_user_input("Enter the EndPoint number: ")
            mycluster = await read_user_input("Enter the Cluster number: ")
            myinout = await read_user_input("Enter the cluster type (in / out): ")
            mycommand = await read_user_input("Enter the command type (0 / 1): ")
            await send_cmd(mydev, myepoint, mycluster, myinout, mycommand )    
        elif user_input.lower() == 'ci':
            user_input = await read_user_input("Enter the Cluster number: ") 
            await cluster_info(user_input)     
        else:
            print("Try it again.")
    # If the application does not run for at least 120 s, it reports an error on exit. Does it turn off something that hasn't had time to start regularly yet?
    # Database engine may fail to start/stop. A rerun error means an inconsistent database?        
    await app.shutdown()
    # await asyncio.sleep(120)
    print("Application closed.")
    
if __name__ == "__main__":
    asyncio.run(main())