# Read values
## Aranet4 info
Service UUID: `0000fce0-0000-1000-8000-00805f9b34fb`
Service UUID before v1.2.0: `f0cd1400-95da-4f4b-9ac8-aa55d312af0c`

| Characteristic UUID                    | Name                              | Type       | Return bytes                           | Values                           |
|----------------------------------------|-----------------------------------|------------|----------------------------------------|----------------------------------|
| `f0cd1401-95da-4f4b-9ac8-aa55d312af0c` | Sensor settings state             | raw        |                                        |                                  |
| `f0cd1503-95da-4f4b-9ac8-aa55d312af0c` | Current Readings                  | raw        | SS:SS:TT:TT:UU:UU:VV:WW:XX             | See Aranet4 readings table       |
| `f0cd3001-95da-4f4b-9ac8-aa55d312af0c` | Current Readings + Interval + Ago | raw        | SS:SS:TT:TT:UU:UU:VV:WW:XX:YY:YY:ZZ:ZZ | See Aranet4 readings table       |
| `f0cd1504-95da-4f4b-9ac8-aa55d312af0c` | Aranet2/Rad Current Readings      | raw        | See Aranet2/Rad readings table         | See Aranet2/Rad readings table   |
| `f0cd2002-95da-4f4b-9ac8-aa55d312af0c` | Read Interval                     | u16LE      | XX:XX                                  | Read interval in seconds         |
| `f0cd1502-95da-4f4b-9ac8-aa55d312af0c` | Sensor callibration data          | raw        | FF:FF:FF:FF:FF:FF:FF:FF                |                                  |
| `f0cd2004-95da-4f4b-9ac8-aa55d312af0c` | Seconds since update              | u16LE      | XX:XX                                  | Last reading time (seconds ago)  |
| `f0cd2001-95da-4f4b-9ac8-aa55d312af0c` | Total readings                    | u16LE      | XX:XX                                  | XX:XX - Total readings in memory |

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
| ZZ:ZZ     | Age (seconds ago)               | uLE16 | not required |

### Aranet2 readings (GATT)
| Parameter | Name                            | Type  | Maths        |
|-----------|---------------------------------|-------|--------------|
| SS:SS     | _Unknown_                       | uLE16 | not required |
| TT:TT     | Interval in seconds             | uLE16 | not required |
| UU:UU     | Age (seconds ago)               | uLE16 | not required |
| VV        | Battery                         | u8    | not required |
| WW:WW     | Temperature                     | uLE16 | /20          |
| XX:XX     | Humidity                        | uLE16 | /10          |
| YY        | Status Flags                    | u8    | not required |

### Aranet2 readings (Advertisement)
| Parameter | Name                            | Type  | Maths        |
|-----------|---------------------------------|-------|--------------|
| header    | Advertisement data header       |       | not required |
| QQ:QQ     | _Unknown_                       | uLE16 | not required |
| RR:RR     | Temperature                     | uLE16 | /20          |
| SS:SS     | _Unknown_                       | uLE16 | not required |
| TT:TT     | Humidity                        | uLE16 | /10          |
| UU        | _Unknown_                       | u8    | not required |
| VV        | Battery                         | u8    | not required |
| WW        | Status Flags                    | u8    | not required |
| XX:XX     | Interval in seconds             | u8    | not required |
| YY:YY     | Age (seconds ago)               | uLE16 | not required |
| ZZ        | Counter                         | u8    | not required |

### Aranet Radiation readings (GATT)
| Parameter   | Name                            | Type  | Maths        |
|-------------|---------------------------------|-------|--------------|
| RR:RR       | _Unknown_                       | uLE16 | not required |
| SS:SS       | Interval in seconds             | uLE16 | not required |
| TT:TT       | Age (seconds ago)               | uLE16 | not required |
| VV          | Battery                         | u8    | not required |
| WW:WW:WW:WW | Radiation dose rate (nSv)       | uLE32 | not required |
| XX:XX:XX:XX:XX:XX:XX:XX | Radiation dose total (nSv)      | uLE64 | not required |
| YY:YY:YY:YY:YY:YY:YY:YY | Total dose duration (seconds)   | uLE64 | not required |
| ZZ          | Status                          | u8    | not required |

### Aranet Radiation readings (Advertisement)
| Parameter   | Name                            | Type  | Maths        |
|-------------|---------------------------------|-------|--------------|
| header      | Advertisement data header       |       |              |
| RR:RR:RR:RR | Radiation dose total (nSv)      | uLE32 | not required |
| SS:SS:SS:SS | Total dose duration (seconds)   | uLE32 | not required |
| TT:TT       | Radiation dose rate (nSv)       | uLE16 | *10          |
| UU          | _Unknown_                       | u8    |              |
| VV          | Battery                         | u8    | not required |
| WW          | _Unknown_                       | u8    |              |
| XX:XX       | Interval                        | u8    | not required |
| YY:YY       | Age (seconds ago)               | u8    | not required |
| ZZ          | Counter                         | u8    | not required |

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

| Characteristic UUID                    | Name                           | Type | Write value             | Parameters                                                                                    |
|----------------------------------------|--------------------------------|------|-------------------------|-----------------------------------------------------------------------------------------------|
| `f0cd1402-95da-4f4b-9ac8-aa55d312af0c` | Set Interval                   | raw  | 90:XX                   | XX - Time in minutes (01,02,05,0A)                                                            |
| `f0cd1402-95da-4f4b-9ac8-aa55d312af0c` | Toggle Smart Home integrations | raw  | 91:XX                   | XX - 0 = disabled, 1 = enabled                                                                |
| `f0cd1402-95da-4f4b-9ac8-aa55d312af0c` | Set Bluetooth range            | raw  | 92:XX                   | XX - 0 = standart, 1 = extended                                                               |
| `f0cd1402-95da-4f4b-9ac8-aa55d312af0c` | Set history parameter          | raw  | 82:XX:00:00:YY:YY:ZZ:ZZ | XX - Property (1,2,3,4), YY:YY - First index (uLE16, starts with 1),ZZ:ZZ - Max index (u16LE) |


