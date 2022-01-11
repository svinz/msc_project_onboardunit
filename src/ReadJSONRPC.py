import logging

import aiohttp

LOG = logging.getLogger("obu")

class teltonikaRUT9x:
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        await self._get_session_id()
        return self

    async def __aexit__(self,exc_type,exc,tb):
        await self.session.close()

    def __init__(self,url,username="root",password=""):
        """Makes an teltonikaRUT9x object to read JSON_RPC from the RUT9x mobile router.
        
        Parameters
        ----------
        url : string
            URL to router
        username : string
            username to log into the router, default: root
        password : string
            Password for username, default: ""
        """

        self._url = url
        payload = { 
            "jsonrpc": "2.0", 
            "id": 1, 
            "method": "call", 
            "params": [ 
                "00000000000000000000000000000000", 
                "session", 
                "login",
                    {"username": "", "password": "", "timeout": 0 } 
                    ] 
                }
        payload["params"][3]["username"] = username
        payload["params"][3]["password"] = password
        
        self.payload = payload
       
    async def _get_session_id(self):
        async with self.session.post(self._url,json=self.payload) as resp:
            LOG.info("Request JSON-RPC session ID from router")
            resp = await resp.json()
            self._sessionId = resp["result"][1]["ubus_rpc_session"]
            LOG.info("Session id retrieved")
        
    async def readSignalStrength(self):
        """
        Reads the RSRP, SINR and RSRQ from the RUT9x 

        Returns
        -------
            dict: with RSRP, SINR and RSPQ.
        """

        payload = {
            "jsonrpc": "2.0", "id": 1, "method": "call", "params":
            [ 
                "",
                "file",
                "exec",
                {
                    "command":"gsmctl",
                    "params":["-WZM" ]
                }
            ]
            }
        payload["params"][0] = self._sessionId
        
        async with self.session.post(self._url,json=payload) as r:
            r = await r.json()
        
        stdout = r["result"][1]["stdout"].split("\n")
        
        result = {
            "RSRP" : "",
            "SINR" : "",
            "RSRQ" : ""
            }
        i = 0
        for x in result:
            result[x] = stdout[i]
            i += 1
        #print(result)
        LOG.info(result)
        return result

    async def readGPS(self):
        """ Reads the latitude and longitude

        Returns
        -------
        dict:
            a dict with the latitude and longitude        
        """

        payload = {
            "jsonrpc": "2.0", "id": 1, "method": "call", "params":
            [ 
                "",
                "file",
                "exec",
                {
                    "command":"gpsctl",
                    "params":["-ix" ]
                }
            ]
            }
        payload["params"][0] = self._sessionId
        #payload = json.dumps(payload)
        #print(payload)
        async with self.session.post(self._url,json=payload) as r:
            r = await r.json()
        #print(r.text)
        stdout = r["result"][1]["stdout"].split("\n")
        #print(stdout)
        result = {
            "Lat" : "",
            "Lon" : ""
            }
        i = 0
        for x in result:
            result[x] = stdout[i]
            i += 1
        #print(result)
        LOG.info(result)
        return result
        