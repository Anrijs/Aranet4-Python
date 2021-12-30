# Read values
## Aranet4 info
Service UUID: `f0cd1400-95da-4f4b-9ac8-aa55d312af0c`

| Characteristic UUID                  | Handle | Name                              | Type       | Return bytes                           | Values                           |
|--------------------------------------|--------|-----------------------------------|------------|----------------------------------------|----------------------------------|
| `f0cd1401-95da-4f4b-9ac8-aa55d312af0c` | 0x0027 | Sensor settings state             | raw        |                                        |                                  |
| `f0cd1503-95da-4f4b-9ac8-aa55d312af0c` | 0x002B | Current Readings                  | raw        | SS:SS:TT:TT:UU:UU:VV:WW:XX             | See readings table               |
| `f0cd3001-95da-4f4b-9ac8-aa55d312af0c` | 0x0038 | Current Readings + Interval + Ago | raw        | SS:SS:TT:TT:UU:UU:VV:WW:XX:YY:YY:ZZ:ZZ | See readings table               |
| `f0cd2002-95da-4f4b-9ac8-aa55d312af0c` | 0x002F | Read Interval                     | u16LE      | XX:XX                                  | Read interval in seconds         |
| `f0cd1502-95da-4f4b-9ac8-aa55d312af0c` | 0x0032 | Sensor callibration data          | raw        | FF:FF:FF:FF:FF:FF:FF:FF                |                                  |
| `f0cd2004-95da-4f4b-9ac8-aa55d312af0c` | 0x0036 | Seconds since update              | u16LE      | XX:XX                                  | Last reading time (seconds ago)  |
| `f0cd2001-95da-4f4b-9ac8-aa55d312af0c` | 0x002D | Total readings                    | u16LE      | XX:XX                                  | XX:XX - Total readings in memory |


### Aranet4 readings
| Parameter | Name                            | Type  | Maths        |
|-----------|---------------------------------|-------|--------------|
| SS:SS     | CO2                             | uLE16 | not required |
| TT:TT     | Temperature                     | uLE16 | /20          |
| UU:UU     | Pressure                        | uLE16 | /10          |
| VV        | Humidity                        | u8    | not required |
| WW        | Battery                         | u8    | not required |
| XX        | Status color (1 - green, 2 - yellow, 3 - red)  | u8    | not required |
| YY:YY     | Interval in seconds             | uLE16 | not required |
| ZZ:ZZ     | Last reading time (seconds ago) | uLE16 | not required |

## Generic info
| Service UUID                         | Characteristic UUID                  | Name              | Type   |
|--------------------------------------|--------------------------------------|-------------------|--------|
| `00001800-0000-1000-8000-00805f9b34fb` | `00002a00-0000-1000-8000-00805f9b34fb` | Device name       | String |
| `0000180a-0000-1000-8000-00805f9b34fb` | `00002a19-0000-1000-8000-00805f9b34fb` | Battery level     | u8     |
| `0000180a-0000-1000-8000-00805f9b34fb` | `00002a24-0000-1000-8000-00805f9b34fb` | Model Number      | String |
| `0000180a-0000-1000-8000-00805f9b34fb` | `00002a25-0000-1000-8000-00805f9b34fb` | Serial No.        | String |
| `0000180a-0000-1000-8000-00805f9b34fb` | `00002a27-0000-1000-8000-00805f9b34fb` | Hardware Revision | String |
| `0000180a-0000-1000-8000-00805f9b34fb` | `00002a28-0000-1000-8000-00805f9b34fb` | Software Revision | String |
| `0000180a-0000-1000-8000-00805f9b34fb` | `00002a29-0000-1000-8000-00805f9b34fb` | Manufacturer Name | String |

# Write values
Service UUID: `f0cd1400-95da-4f4b-9ac8-aa55d312af0c`

| Characteristic UUID                  | Handle | Name                  | Type | Write value             | Parameters                                                                                    |
|--------------------------------------|--------|-----------------------|------|-------------------------|-----------------------------------------------------------------------------------------------|
| `f0cd1402-95da-4f4b-9ac8-aa55d312af0c` | 0x0029 | Set Interval          | raw  | 90:XX                   | XX - Time in minutes (01,02,05,0A)                                                            |
| `f0cd1402-95da-4f4b-9ac8-aa55d312af0c` |        | Set history parameter | raw  | 82:XX:00:00:YY:YY:ZZ:ZZ | XX - Property (1,2,3,4), YY:YY - First index (uLE16, starts with 1),ZZ:ZZ - Max index (u16LE) |


