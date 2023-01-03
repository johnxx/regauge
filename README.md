# re:Gauge

## Overview
_re:Gauge_ is a CircuitPython codebase designed to pull in data from anywhere and display it any way you want. Right now it has support for several data sources:
- Directly attached CANbus
- MSGPack data sent over TCP
- SCD41x temperature/humidity/CO2 sensors
- PMSA003i air quality sensors
- Any sensor that's read by counting pulses
- A "mock" data source for testing

And several different ways to visualize the data (what I've taken to calling "gauge faces"):
- a simple `text` gauge face for showing the current data (for LCDs)
- a `line_graph` gauge face to show how the data has changed over time (for LCDs)
- a modern-looking gauge face designed for circular LCDs I call `alpha`
- and a gauge face that uses NeoPixel-compatible RGB LEDs called `multi_led`

The codebase is designed to make it easy to add your own data sources and gauge faces and I intend to write a lot more of both as time goes on. 

## Quickstart
1. Download the [latest release](https://github.com/johnxx/regauge/releases)
1. Copy the contents of the archive to your CircuitPython device, replacing any files that are already on the device.
1. To get started, copy the `config.d` folder from the `examples/mock_demo` folder to your CircuitPython device
## Upgrades
## Concept & Code Structure
