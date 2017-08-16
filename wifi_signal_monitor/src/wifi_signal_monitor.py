from utime import sleep

from machine import Pin, PWM
import network

# The CPython "colorsys" module must be loaded onto the device (see
# https://raw.githubusercontent.com/python/cpython/master/Lib/colorsys.py)
from colorsys import hsv_to_rgb


# The pin numbers to which the RGB LED is connected (see
# https://github.com/nodemcu/nodemcu-devkit-v1.0#pin-map)
RGB_LED_PIN_NUMS = (14, 12, 13)

# The PWM frequency in the range of 1 to 1000 hertz
PWM_FREQUENCY = 120

# The value corresponding to a 100% PWM duty cycle
PWM_FULL_DUTY_CYCLE = 1023

# The access point names to monitor
MONITORED_SSIDS = (b'AndroidAP',)

# The range of expected RF signal strengths (see
# https://en.wikipedia.org/wiki/Received_signal_strength_indication)
RSSI_MIN, RSSI_MAX = -80, -30


# RF signal strengths are distributed on a one-dimensional scale.  The more
# negative the signal strength, the weaker the RF signal is.  To drive an RGB
# LED, a signal strength must be mapped to the three-dimensional RGB color
# space.  This is most easily done by scaling the signal strength within a
# defined range, and then using the HSV to RGB color mapping algorithm, where
# the scaled signal strength is treated as the hue (see
# https://en.wikipedia.org/wiki/HSL_and_HSV).  The last sixth of the color
# wheel is ignored as to avoid the color wrapping around and making the best
# and worst signals appear as the same color.
def rssi_to_rgb(rssi):
    scaled_rssi = (rssi - RSSI_MIN) / (RSSI_MAX - RSSI_MIN)
    scaled_rssi = min(1.0, max(0.0, scaled_rssi))
    scaled_rssi *= 5 / 6

    rgb_tuple = hsv_to_rgb(scaled_rssi, 1.0, 1.0)

    print('rssi = %d, scaled_rssi = %f, rgb_tuple = %s' % (rssi, scaled_rssi, rgb_tuple))

    return rgb_tuple


# Initialize the physical hardware pins to which the RGB LED is connected.
# There is one pin for each RGB color channel.
pins = tuple(Pin(pin_num, Pin.OUT) for pin_num in RGB_LED_PIN_NUMS)

# A pin, and hence one of the RGB LED's color channels, can instaneously only
# be on or off.  By using PWM, or Pulse Width Modultation (see
# https://en.wikipedia.org/wiki/Pulse-width_modulation), the perception that a
# color channel is only partially illuminated can be created.
pwms = tuple(PWM(pin) for pin in pins)

# Initialize the wi-fi client interface (i.e. station interface)
station_if = network.WLAN(network.STA_IF)
station_if.active(True)

# The main loop continuously performs the following steps:
#     - Scan for wi-fi access points with one of the defined names
#     - Calculate the greatest RF signal strength
#     - Convert the RF signal strength to an RGB tuple
#     - Set the PWM duty cycle for each of the RGB LED's color channels as to
#       render the color described by the RGB tuple
while True:
    access_points = station_if.scan()
    access_points = [access_point for access_point in access_points if access_point[0] in MONITORED_SSIDS]

    rssi = max([access_point[3] for access_point in access_points]) if len(access_points) > 0 else RSSI_MIN

    rgb_tuple = rssi_to_rgb(rssi)

    for e in zip(pwms, rgb_tuple):
        e[0].freq(PWM_FREQUENCY)
        e[0].duty(int(PWM_FULL_DUTY_CYCLE * e[1]))

    # Control must be periodically yielded as to reset the watchdog timer
    sleep(0)
