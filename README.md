A four-wheel ESP32 rover project that combines motor control, sensor telemetry, Wi-Fi networking, and a Python ground station.

The project was developed in stages:

A non-blocking scripted movement state machine.

A Wi-Fi TCP version that sends live telemetry and accepts movement commands from a Python program.

Current Status

Working

Four-wheel differential drive

TB6612FNG motor control

Non-blocking movement using millis()

DHT22 temperature and humidity readings

MPU6050 accelerometer and gyroscope readings

Photoresistor light readings

LED status output

Wireless TCP telemetry over Wi-Fi

Python telemetry receiver

Automatic TCP reconnection

Separate power sources for the ESP32 and motors

In Progress

Reliable manual movement through the Python controller

Forward and backward command troubleshooting

Ultrasonic obstacle detection

Autonomous obstacle avoidance

Hardware

ESP32 DevKit V1

Four-wheel TT motor chassis

TB6612FNG motor driver

DHT22 temperature and humidity sensor

MPU6050 accelerometer and gyroscope

Photoresistor

LED

Motor battery pack

USB power bank for the ESP32

Breadboard and jumper wires

Pin Configuration

Motor Driver

Function

ESP32 Pin

PWMA

25

AIN1

26

AIN2

27

PWMB

33

BIN1

32

BIN2

13

STBY

14

Sensors

Component

ESP32 Pin

DHT22 data

4

Photoresistor

36

LED

23

MPU6050 SDA

21

MPU6050 SCL

22

Power Setup

USB power bank ─────────────> ESP32

Motor battery positive ─────> TB6612FNG VM
Motor battery negative ─────> TB6612FNG GND

ESP32 GND ──────────────────> TB6612FNG GND

The ESP32 and motor driver use separate power sources, but they must share a common ground.

Repository Structure

esp32-wireless-rover/
├── firmware/
│   ├── scripted_motion/
│   │   └── scripted_motion.ino
│   └── manual_tcp_control/
│       └── manual_tcp_control.ino
├── python/
│   ├── rover_receiver.py
│   └── rover_controller_tkinter.py
├── README.md
└── .gitignore

Firmware Versions

1. Scripted Motion

firmware/scripted_motion/scripted_motion.ino

This version demonstrates a non-blocking movement state machine.

The rover repeatedly performs:

Forward
→ Stop
→ Backward
→ Stop
→ Turn left
→ Stop
→ Turn right
→ Stop
→ Repeat

The sequence uses millis() instead of long delay() calls, allowing other tasks to run while the rover is moving.

2. Manual TCP Control

firmware/manual_tcp_control/manual_tcp_control.ino

This version adds:

Wi-Fi connectivity

A TCP server on port 5000

Wireless telemetry

Python command input

A command timeout safety feature

Automatic Wi-Fi reconnection

Safe stopping when the controller disconnects

Supported commands:

FORWARD
BACKWARD
LEFT
RIGHT
STOP

Each command is sent as a newline-terminated TCP message.

Example:

FORWARD\n

The rover starts in the stopped state and waits for the Python controller.

Wireless Telemetry

The ESP32 sends one CSV telemetry packet every two seconds.

CSV Header

time_ms,temp_c,humidity_percent,light_raw,light_status,accel_x,accel_y,accel_z,gyro_x,gyro_y,gyro_z,rover_state,system_status

Example Packet

20463,23.60,67.30,594,Dim,-0.01,0.17,9.89,-0.08,0.02,-0.01,STOPPED,LOW_LIGHT

Telemetry Fields

Field

Description

time_ms

ESP32 runtime in milliseconds

temp_c

Temperature in degrees Celsius

humidity_percent

Relative humidity

light_raw

Raw photoresistor reading

light_status

Dark, Dim, Light, Bright, or Very_bright

accel_x/y/z

Acceleration from the MPU6050

gyro_x/y/z

Angular velocity from the MPU6050

rover_state

Current rover movement state

system_status

Overall sensor or warning status

Possible system statuses include:

NOMINAL
DHT_ERROR
THERMAL_WARNING
LOW_LIGHT
MOTION_WARNING

Python Programs

Telemetry Receiver

python/rover_receiver.py

The telemetry receiver:

Connects to the ESP32 TCP server

Displays incoming CSV telemetry

Detects connection loss

Reconnects automatically

Before running it, update the ESP32 IP address:

ESP32_IP = "192.168.12.123"
PORT = 5000

Run:

py .\python\rover_receiver.py

Tkinter Controller

python/rover_controller_tkinter.py

The Tkinter controller:

Uses only Python's standard library

Sends movement commands to the ESP32

Receives telemetry through the same TCP connection

Displays connection status and live sensor data

Sends repeated commands while a key is held

Sends STOP when the key is released

Attempts to reconnect after connection loss

Controls:

W / Up Arrow       Forward
S / Down Arrow     Backward
A / Left Arrow     Turn left
D / Right Arrow    Turn right
Space              Stop
Esc or Q           Exit

Run:

py .\python\rover_controller_tkinter.py

Do not run the standalone receiver and the controller at the same time because the firmware currently uses one TCP client connection.

Arduino Libraries

Install these libraries in Arduino IDE:

DHT Sensor Library

Adafruit MPU6050

Adafruit Unified Sensor

The ESP32 Wi-Fi and Wire libraries are included with the ESP32 Arduino board package.

Wi-Fi Credentials

Do not upload real Wi-Fi credentials to GitHub.

A recommended setup is:

#include "secrets.h"

const char* ssid = WIFI_SSID;
const char* password = WIFI_PASSWORD;

Create a local secrets.h file:

#pragma once

#define WIFI_SSID "YOUR_WIFI_NAME"
#define WIFI_PASSWORD "YOUR_WIFI_PASSWORD"

Add this to .gitignore:

secrets.h
**/secrets.h

You may also include a safe example file named secrets.example.h:

#pragma once

#define WIFI_SSID "YOUR_WIFI_NAME"
#define WIFI_PASSWORD "YOUR_WIFI_PASSWORD"

Safety Features

The manual-control firmware includes several safeguards:

The rover starts stopped.

It stops when the TCP client disconnects.

It stops if movement commands stop arriving.

The Python controller sends STOP when movement keys are released.

The Python controller attempts to send STOP before closing.

During testing, keep the rover's wheels lifted off the ground until direction control is verified.

Engineering Concepts Demonstrated

Embedded C++ programming

Finite-state machines

Non-blocking timing with millis()

PWM motor control

Differential-drive movement

I2C communication

Analog sensor acquisition

TCP client-server networking

CSV telemetry design

Python socket programming

GUI development with Tkinter

Connection-loss handling

Hardware/software integration

Known Limitations

Manual forward and backward commands still require additional debugging.

The rover currently supports one TCP client at a time.

The ESP32 IP address is entered manually in the Python program.

The scripted movement version does not react to obstacles.

The ultrasonic sensor has not yet been integrated into the completed firmware.

Planned Improvements

Finish debugging manual TCP motor control

Add ultrasonic distance sensing

Implement obstacle avoidance

Add a servo-mounted ultrasonic scanner

Add adjustable motor speed

Add a richer telemetry dashboard

Add data logging to CSV

Add mDNS or a static IP

Add autonomous navigation modes

Project Summary

This project demonstrates the progression from basic motor control to a connected embedded rover platform. The ESP32 controls four motors, reads multiple sensors, sends telemetry wirelessly, and communicates with a Python ground station over TCP.

The project is still being developed, but the wireless telemetry system and non-blocking rover architecture provide a strong foundation for future autonomous navigation.
