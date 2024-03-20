from zigpy.config import CONF_DEVICE
import zigpy.config as conf
from zigpy.types.named import EUI64
import zigpy.device

import asyncio
import json

# There are many different radio libraries but they all have the same API
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
    print(f"Čekám na spárování max {duration} sekund.")            
    await asyncio.sleep(int(duration))
    print("Konec párování.")

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
        print("Cluster nenalezen")
        return
    print("Cluster připojen")
    print(mycluster)
    
async def ubind_cmd(a1, a2, a3, a4):
    try:
        mycluster = await get_cluster_from_args(a1, a2, a3, a4).unbind()
    except:
        print("Cluster nenalezen")
        return
    print("Cluster odpojen")

    
async def send_cmd(a1, a2, a3, a4, a5):
    try:
        mycluster = get_cluster_from_args(a1, a2, a3, a4)
        print(mycluster)
    except:
        print("Cluster nenalezen")
        return
    try:
        command_id=int(a5)
    except:
        print("Příkaz musí být číslo")
        return
    await mycluster.command(command_id)
    print("Příkaz odeslán")
 
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
            "path": "COM3",
        }
    }))

    listener = MainListener(app)
    app.add_listener(listener)
    app.groups.add_listener(listener)
    # await app.startup(auto_form=True)
    print("Zigbee je spuštěno.")
    
    # Just run forever
    # await asyncio.get_running_loop().create_future()
    await asyncio.sleep(5)   # prostor pro vypsání zpráv spuštěných procesů
    while True:
        user_input = await read_user_input("Zadej znak (q=konec, l=list, d=device, b=připojení, u=odpojení, p=párování, c=odeslání příkazu, ci=cluster info): ") # asynchronní vstup, neblokuje procesy

        if user_input.lower() == 'q':
            print("Program se ukončuje.")
            break
        elif user_input.lower() == 'l':
            print("Spouštím proceduru list.")
            await devices_list_cmd()
        elif user_input.lower() == 'p':
            user_input = await read_user_input("Zadej dobu čekání na spárování: ")
            print("Spouštím párování.")
            print("Aktivujte u zařízení režim párování.")
            await pair_cmd(user_input)
        elif user_input.lower() == 'd':
            user_input = await read_user_input("Zadej číslo zařízení: ") 
            await devices_cmd(user_input)  
        elif user_input.lower() == 'b':
            mydev = await read_user_input("Zadej číslo Device(1): ") 
            myepoint = await read_user_input("Zadej číslo EndPoint(2): ")
            mycluster = await read_user_input("Zadej číslo Clusteru(6): ")
            myinout = await read_user_input("Zadej typ clusteru(in): ")
            await bind_cmd(mydev, myepoint, mycluster, myinout )
        elif user_input.lower() == 'u':
            mydev = await read_user_input("Zadej číslo Device(1): ") 
            myepoint = await read_user_input("Zadej číslo EndPoint(2): ")
            mycluster = await read_user_input("Zadej číslo Clusteru(6): ")
            myinout = await read_user_input("Zadej typ clusteru(in): ")
            await ubind_cmd(mydev, myepoint, mycluster, myinout )    
        elif user_input.lower() == 'c':
            mydev = await read_user_input("Zadej číslo Device(1): ") 
            myepoint = await read_user_input("Zadej číslo EndPoint(2): ")
            mycluster = await read_user_input("Zadej číslo Clusteru(6): ")
            myinout = await read_user_input("Zadej typ clusteru(in): ")
            mycommand = await read_user_input("Zadej typ příkazu(0 / 1): ")
            await send_cmd(mydev, myepoint, mycluster, myinout, mycommand )    
        elif user_input.lower() == 'ci':
            user_input = await read_user_input("Zadej číslo clusteru: ") 
            await cluster_info(user_input)     
        else:
            print("Neznámý znak. Zkus to znovu.")
    # Pokud aplikace neběží alespoň 120 s, při ukončení hlásí chybu, že vypíná něco, co nejede (ještě se nestihlo spustit ???)
    await app.shutdown()
    # await asyncio.sleep(120)
    print("Applikace ukončena.")
    
if __name__ == "__main__":
    asyncio.run(main())