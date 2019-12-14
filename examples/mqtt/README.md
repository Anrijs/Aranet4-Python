# MQTT Example

## mqtt.py
This example read data from aranet and then sends it to mqtt broker.

### Usage
Send to host, with topic: `python publish.py DEVICE_ADDRESS HOSTNAME TOPIC_BASE [OPTIONS]`

Options:
```
  -P  <port>      Broker port
  -u  <user>      Auth user name
  -p  <password>  Auth user password
```

Data will be sent to `TOPIC_BASE`/`<sensor_name>`.

For example, if `TOPIC_BASE` is set to "bedroom/aranet4/, following data will be sent:
```
/bedroom/aranet4/temperature
/bedroom/aranet4/pressure
/bedroom/aranet4/humidity
/bedroom/aranet4/co2
/bedroom/aranet4/battery
```

#### Automatic data collection

To automate data collection, using crontab will be easiest way:
1. Edit crontab: `crontab -e`

2. Add job. If running Aranet4 with 1 minute intervals, run script every minute:`* * * * * python /PATH_TO_THIS_FILE/publish.py XX:XX:XX:XX:XX:XX bedroom/ar4/ HOSTNAME`

3. Save and close crontab.
