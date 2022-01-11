import logging
import aiohttp
import json
LOG = logging.getLogger("obu")

class mikrotik:
    def __init__(self,hostname,username,password):
        self.hostname = hostname
        self.username = username
        if password == None: #Aiohttp doesnt accept None as password, setting it to "" if that is the case
            self.password = ""
        else:
            self.password = password

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()

    async def __aexit__(self,*exc_info):
        await self.session.close()
    
    async def readSignalStrength(self):
        payload = {"numbers":"0","once":""}
        self._url = self.hostname +"/rest/interface/lte/monitor"
        # equals sending ssh command: interface lte monitor 0 once
        async with self.session.post(self._url,auth=aiohttp.BasicAuth(self.username, self.password),json=payload,ssl=False) as r:
            r = await r.text() 
        r = json.loads(r)
        #take the first element, we are running this once, so there is only one element, but i could have been runned for some
        # time and then the result would include several elements
        LOG.info(r[0])
        return r