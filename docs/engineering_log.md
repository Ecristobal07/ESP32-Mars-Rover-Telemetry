## 7/15/2026
# Goal
- Make Chassis
- Make motor drive

# What I did
- Installed motors on the pcb chassis
- Verified TTB6 driver motor


# Investigation
-Followed tutorial on how to assemble four motors onto pcb chassis
-Followed tutorial on how to test driver motor
-Used 8v for vm and 5v for vcc
- breadboard for the driver motor

# Conclusion
The chassis is built and the TTB6 works. Therefore the motor is able to make the wheel spin.

# What I learned
- Stripping wires can be a nuissance
- Make sure to use a dmm to check for proper voltage, i.e make sure there is no random voltage drops and no unsafe levels of voltage
- As long as the copper touches the metal the motor will work, just make sure to wrap it nicely
- This took a lot longer than expected.

## 7/21/2026
# Goal
-Power all 4 motors using ttb6
- code drivetrain (tank style)
- Integrate telemetry

# What I did
- Combined Left_Front and Left_rear to One channel of TB66\
- Combined Right_Front and Right_Rear to one channel of TB66
- Confirmed all four motors worked
- Used AI to create the testing code
- Cleaned up wiring

# What I learned
Tank style driving is a type where one channel controls the whole left side and the other the whole right side.
