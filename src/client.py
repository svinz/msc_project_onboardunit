import asyncio
import ssl
import sys
import signal
import click
import yaml
from asyncio_mqtt import MqttError

import logconfig
import mqtt
from TLScontext import TLScontext

LOG = logconfig.init_logging("obu")
#using click to specify the configfile with all config details, using built in function in click to verify that file exist
@click.command()
@click.option("-config", help="Path to configfile", required=True, type=click.Path(exists=True))

def main(config):

    try:
        with open(config,'r') as f:
            cfg = yaml.safe_load(f) #Open file and load content to cfg
    except yaml.scanner.ScannerError as e:
        LOG.error("Error reading file: {}".format(config))
        sys.exit(1)    

    loop = asyncio.get_event_loop()
    signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
    for s in signals:
        loop.add_signal_handler(
            s, lambda s=s: asyncio.create_task(shutdown(loop,signal=s)))
    loop.set_exception_handler(handle_exception)

    #while True: #Run until it stops
    try:
        loop.create_task(start_mqtt(cfg))
        loop.run_forever()
    finally:
        loop.close()
        LOG.info("Shutting down onboard unit")

async def start_mqtt(cfg):
    #create TLScontext, passing the paths to the files stated in the configfile
    context =  TLScontext.create_tls_context(ca_certs=cfg["ca_cert"], 
        certfile=cfg["certfile"], 
        keyfile=cfg["keyfile"], 
        cert_reqs=ssl.CERT_REQUIRED)
    while True:
        try:
            await mqtt.handler(mqtt_hostname=cfg["MQTT_URL"],
                mqtt_port=cfg["MQTT_port"],
                logger=LOG,
                context=context,
                topics=cfg["Topics"],
                router_cfg=cfg["router"],sslkeylog=cfg["SSLKEYLOG"])
        except MqttError as error:
            print(f'Error "{error}". Reconnecting in seconds.')
            await asyncio.sleep(1) 

async def shutdown(loop,signal=None):
    if signal:
        LOG.info(f"Received exit signal {signal.name}...")
    LOG.info("Cancelling all tasks")
    tasks = [t for t in asyncio.all_tasks() if t is not
             asyncio.current_task()]
    for task in tasks:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    #[task.cancel() for task in tasks]

    LOG.info(f"Cancelling {len(tasks)} outstanding tasks")
    await asyncio.gather(*tasks, return_exceptions=True)
    LOG.info(f"Flushing metrics")
    loop.stop()

def handle_exception(loop, context):
    msg = context.get("exception", context["message"])
    LOG.error(f"Caught exception: {msg}")
    LOG.info("Shutting down...")
    asyncio.create_task(shutdown(loop))

#if __name__ == "__main__":
main() # pylint: disable=unexpected-keyword-arg
