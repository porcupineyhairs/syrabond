import mqttsender

pinger = mqttsender.Mqtt('mqtt_globalpinger')
pinger.mqttsend(pinger.ping_topic, 'PING')