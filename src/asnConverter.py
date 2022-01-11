import asn1tools
from datetime import datetime

timestamp20040101_in_ms = 1072915200000 #milliseconds since start of Unix time to 2004-01-01T00:00:00.000Z.

class CAM:
    def __init__(self):
        self._cam = asn1tools.compile_files("ETSImessages/ETSI CAM v1.4.1.asn","uper")
        self.message = {
                "header": {
                    "protocolVersion":1,
                    "messageID": 1,
                    "stationID": 1234567
                },
                "cam":{
                    "generationDeltaTime": 11409,
                        "camParameters":{
                            "basicContainer":{
                                "stationType" : 5,
                                "referencePosition": {
                                    "latitude": 40487111,
                                    "longitude": 79494789,
                                        "positionConfidenceEllipse":{
                                            "semiMajorConfidence": 500,
                                            "semiMinorConfidence": 400,
                                            "semiMajorOrientation": 0
                                        },
                                    "altitude": {
                                        "altitudeValue":2000,
                                        "altitudeConfidence": "alt-000-02"
                                    }
                                }
                            },
                            "highFrequencyContainer":(
                                "basicVehicleContainerHighFrequency",{
                                    "heading": {
                                        "headingValue": 0,
                                        "headingConfidence": 1
                                    },
                                    "speed":{
                                        "speedValue": 2000,
                                        "speedConfidence": 1
                                    },
                                    "driveDirection": "forward",
                                    "vehicleLength":{
                                        "vehicleLengthValue": 50,
                                        "vehicleLengthConfidenceIndication":"noTrailerPresent"
                                    },
                                    "vehicleWidth":50,
                                    "longitudinalAcceleration":{
                                        "longitudinalAccelerationValue":10,
                                        "longitudinalAccelerationConfidence":1
                                    },
                                    "curvature":{
                                        "curvatureValue":0,
                                        "curvatureConfidence":"onePerMeter-0-00002"
                                    },
                                    "curvatureCalculationMode":"yawRateUsed",
                                    "yawRate": {
                                        "yawRateValue":0,
                                        "yawRateConfidence":"degSec-000-01"
                                    }
                                }
                            )
                        }
                    }
                }

    def encode(self):
        return self._cam.encode("CAM",self.message)

    def decode(self,message):
        
        return self._cam.decode("CAM",message)

    def set_generationTimeDelta(self):
        #conveniencefunction to generate time
        self.message["cam"]["generationDeltaTime"] = round((datetime.now().microsecond - timestamp20040101_in_ms *1000) % 65536)

class DENM:
    def __init__(self):
        self._denm = asn1tools.compile_files("ETSImessages/ETSI DENM v1.3.1.asn")
        self.message = {
            "header": {
                "protocolVersion":1,
                "messageID": 1,
                "stationID": 1234567
            },
        }
    
    def encode(self,message):
        return self._denm.encode("DENM",message)

    def decode(self,message):
        return self._denm.decode("DENM",message)