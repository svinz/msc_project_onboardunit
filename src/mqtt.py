import asyncio
import logging
import uuid
from contextlib import AsyncExitStack
import json
from asyncio_mqtt import Client, MqttError
import sslkeylog

from aiogps import aiogps


LOG = logging.getLogger("obu")


async def logSignal(router,interval):
    while True:
        #reads the signal strength at every interval
        await router.readSignalStrength()
        await asyncio.sleep(interval)

async def sendPosition(client,gpsd,topic,qos):
    limiter = 0
    async for result in gpsd:

        if "device" in result:
            if result["class"] == "SKY" and result["device"] == "/dev/ttyACM0" and limiter > 10:
                limiter = 0
                LOG.info(result)
            elif result["class"] == "SKY" and result["device"] == "/dev/ttyACM0" and limiter <= 10:
                limiter += 1
            elif result["class"] != "SKY" and result["device"] != "/dev/ttyACM0":
                LOG.info(result)
            elif result["class"] == 'TPV' and ("track" in result) and result["device"] == "/dev/ttyACM0": # check that we get the object with the postioin
                result["uuid"] = uuid.uuid4().__str__()  #generate a unique string
                result["GPS_time"] = result.pop("time")
                try:
                    #delete alot to reduce the message size to hit around 400bytes
                    del result["sep"], result["eph"], result["geoidSep"], result["ecefvAcc"],result["ecefpAcc"],result["ecefvz"],result["ecefvy"],result["ecefvx"],
                    del result["ecefz"],result["ecefy"],result["ecefx"],result["epc"],result["eps"]
                except:
                    pass
                #Log the result directly as an dict to ensure it gets nicely converted to a a JSON in the log
                result["mqtt_topic"] = topic
                LOG.info(result) # include the topic in the log eased logreading

                result = json.dumps(result) #convert to a json formatted string
                await client.publish(topic,result,qos) # publish it to broker    
        else:
            LOG.info(result)

async def logSSLKEYLOG(client,sslkey_config):
    sslkeylogfile = {"KeyLogLine": ""}
    while True:
        # not a very effective way of checking if a reconnect has occured, but there was no callbacks available
        # from the asyncio_mqtt library. 
        keylog = sslkeylog.get_keylog_line(client._client._sock)
        if sslkeylogfile["KeyLogLine"] == keylog:
            pass
        else:
            sslkeylogfile["KeyLogLine"] = keylog
            try:
                with open(sslkey_config["filename"],"a") as f:
                    f.write(sslkeylogfile["KeyLogLine"]+"\n")
            except:
                pass
            LOG.info(sslkeylogfile)
        await asyncio.sleep(60)
            
async def log_messages(messages):
    async for message in messages:
        # 🤔 Note that we assume that the message paylod is an
        # UTF8-encoded string (hence the `bytes.decode` call).
        #respone = bytearray.fromhex(message.payload)
        response = message.payload.decode()
        response = json.loads(response)
        response["mqtt_topic"] = message.topic # add the topic to the dict to ease the log analyze
        LOG.info(response)

async def cancel_tasks(tasks):
    for task in tasks:
        if task.done():
            continue
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

async def handler(mqtt_hostname, mqtt_port, logger,context,topics,router_cfg,sslkeylog):
    # defining an AsyncExitStack as stack to use with the asynccontextmanager
    async with AsyncExitStack() as stack:
        #set up a set of tasks the asyncio shall work through
        tasks = set()
        #defining what the asynccontextmanager shall do upon exit.
        stack.push_async_callback(cancel_tasks,tasks)
        #using the clientID as both clientID and base topic
        clientID = "OBU" + uuid.uuid4().hex
        #TODO: Fix the asyncio_MQTT library with tuples to pass the certificates. 
        #initializing a MQTT client
        client = Client(mqtt_hostname,mqtt_port,logger=logger,tls_context=context,client_id=clientID)

        if router_cfg["4GRouter"]["enabled"]:
            from ReadJSONRPC import teltonikaRUT9x
            router = teltonikaRUT9x(router_cfg["4GRouter"]["hostname"],router_cfg["4GRouter"]["username"],router_cfg["4GRouter"]["password"])
            await stack.enter_async_context(router)
            #add the signallogging to the async tasks
            task = asyncio.create_task(logSignal(router,1))
            tasks.add(task)

        if router_cfg["5GRouter"]["enabled"]:
            from mikrotik import mikrotik
            router5G = mikrotik(router_cfg["5GRouter"]["hostname"],router_cfg["5GRouter"]["username"],router_cfg["5GRouter"]["password"])
            await stack.enter_async_context(router5G)
            task = asyncio.create_task(logSignal(router5G,2))
            tasks.add(task)
        # set up an instance of the GPS
        gpsd = aiogps()
        await stack.enter_async_context(gpsd)
        #putting the client into the asynccontextmanager
        LOG.info("Connect to MQTT-broker")
        await stack.enter_async_context(client)
        #Loop through all topics that we shall subscribe to
        topic_filters= topics["subscribe"]
        for topic_filter in topic_filters:
            #Use the filtered_messages to make an async generator 
            manager = client.filtered_messages(topic_filter)
            #put the generator into the asynccontextmanager 
            messages = await stack.enter_async_context(manager)
            #template = f'[topic_filter="{topic_filter}"] {{}}'
            #set up a task 
            task = asyncio.create_task(log_messages(messages))
            tasks.add(task)
        #Make a list of topics with Qos 0 to feed into the client.subscribe
        subscribe_topics = []
        for i in topic_filters:
            subscribe_topics.append((i,0))
        await client.subscribe(subscribe_topics)

        #create a task that sends the position on the MQTT with the clientID as a basis for topic
        task = asyncio.create_task(sendPosition(client,gpsd,topics["publish"][0],0))
        tasks.add(task)

        # task for checking for new SSLkeylog lines
        task = asyncio.create_task(logSSLKEYLOG(client,sslkeylog))
        tasks.add(task)
        # Wait for everything to complete (or fail due to, e.g., network
        # errors)
        await asyncio.gather(*tasks)

