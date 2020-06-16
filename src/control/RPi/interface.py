import math
import time

import serial

import xbox
from IK_Engine import Quadruped

#FL, FR, BL, BR
#Hip, Shoulder, Width
joint_positions = [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]]

joy = xbox.Joystick()
# Setting up Quadruped
robot = Quadruped(origin=(0, 0, 0), height=170)
x_shift = y_shift = z_shift = yaw_shift = roll_shift = 0
x_bound = y_bound = z_bound = 50
roll_bound = 20
dampening_rate = 3
max_speed = 150  # deg/sec

alpha = 0.65
prev_joy_x = prev_joy_y = prev_joy_x_r = 0

deadzone = 0.2

ser = serial.Serial('/dev/ttyS0', 115200)
ser.flush()

while not joy.Back():
    data_received = ""
    line = ""
    start_time = time.time()

    # joystick filtering:

    prefilter_x = -joy.leftX()
    prefilter_y = joy.leftY()
    prefilter_x_r = -joy.rightX()

    if prefilter_x < deadzone and prefilter_x > -deadzone:
        prefilter_x = 0
    if prefilter_y < deadzone and prefilter_y > -deadzone:
        prefilter_y = 0
    if prefilter_x_r < deadzone and prefilter_x_r > -deadzone:
        prefilter_x_r = 0

    joy_x = round(alpha * prev_joy_x + (1 - alpha) * prefilter_x, 1)
    joy_y = round(alpha * prev_joy_y + (1 - alpha) * prefilter_y, 1)
    joy_x_r = round(alpha * prev_joy_x_r + (1 - alpha) * prefilter_x_r, 1)

    prev_joy_x = joy_x
    prev_joy_y = joy_y
    prev_joy_x_r = joy_x_r

    x_shift = round(x_bound * joy_y, 1)
    y_shift = round(y_bound * joy_x, 1)
    z_shift += round(dampening_rate * (joy.dpadUp() - joy.dpadDown()), 1)
    roll_shift = round(roll_bound * joy_x_r, 1)
    yaw_shift += round(dampening_rate / 5 *
                       (joy.dpadRight() - joy.dpadLeft()), 1)
    if (z_shift > z_bound):
        z_shift = z_bound
    if (z_shift < -z_bound):
        z_shift = -z_bound
    if (joy.Y()):
        x_shift = y_shift = z_shift = yaw_shift = roll_shift = 0
    if (joy.B()):
        x_shift = y_shift = yaw_shift = roll_shift = 0
        z_shift = -140
    # Going to starting pose
    robot.start_position()
    # Shifting robot pose in cartesian system x-y-z (body-relative)
    robot.shift_body_xyz(x_shift, y_shift, z_shift)
    # Shifting robot pose in Euler Angles yaw-pitch-roll (body-relative)
    robot.shift_body_rotation(math.radians(
        yaw_shift), math.radians(0), math.radians(roll_shift))

    strings_to_send = []
    fl = robot.legs[2]
    fr = robot.legs[1]
    bl = robot.legs[3]
    br = robot.legs[0]
    legs = [fl, fr, bl, br]

    factor = 1

    for i, leg in enumerate(legs):

        desired_x = round(leg.x, 1)
        desired_y = round(leg.y, 1)
        desired_z = round(leg.z, 1)

        strings_to_send.append(
            f'{i},{desired_x},{desired_y},{desired_z}\n')

    print(strings_to_send)
    for message in strings_to_send:
        ser.write(message.encode('utf-8'))
    # print(
    #     f'fps: {round(1/(time.time() - start_time), 1)}, data: {line}')


joy.close()
