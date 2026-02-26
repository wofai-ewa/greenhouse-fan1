# Model viam:greenhouse-fan1:greenhouse-fan1

A temperature-controlled fan switch for greenhouse environments. The model implements the Viam `Switch` component and drives a relay on GPIO pin 27 of a Raspberry Pi. When a temperature sensor dependency is configured, a background loop automatically turns the fan on and off based on configurable temperature thresholds.

## Configuration

```json
{
  "sensor_name": "<string>",
  "temp_on_c": <float>,
  "temp_off_c": <float>,
  "poll_interval": <int>
}
```

### Attributes

| Name            | Type   | Inclusion | Default | Description                                                  |
|-----------------|--------|-----------|---------|--------------------------------------------------------------|
| `sensor_name`   | string | Optional  | —       | Name of the Viam `sensor` component to read temperature from |
| `temp_on_c`     | float  | Optional  | `23.9`  | Temperature (°C) at or above which the fan turns ON (~75°F)  |
| `temp_off_c`    | float  | Optional  | `21.1`  | Temperature (°C) at or below which the fan turns OFF (~70°F) |
| `poll_interval` | int    | Optional  | `10`    | How often (seconds) to check the temperature sensor          |

### Example Configuration

```json
{
  "sensor_name": "temp-sensor-1",
  "temp_on_c": 25.0,
  "temp_off_c": 22.0,
  "poll_interval": 15
}
```

## Switch Positions

| Position | State |
|----------|-------|
| `0`      | OFF   |
| `1`      | ON    |

## DoCommand

Use `set_position` to manually override the fan state.

### Example DoCommand

```json
{
  "set_position": 1
}
```

**Response:**

```json
{
  "position": 1
}
```
