#!/usr/bin/env python3


import asyncio
from pynput import keyboard

from mavsdk import System
from mavsdk.offboard import (OffboardError, VelocityNedYaw)

velocity = None

def on_press(key):
    global velocity
    if key == keyboard.Key.esc:
        return False  # stop listener
    try:
        if key == 'w':
            print ("w press")
            velocity = VelocityNedYaw(2.0, 0.0, 0.0, 0.0)
        else:
            print (key + " pressed, reset speed")
            velocity = VelocityNedYaw(0.0, 0.0, 0.0, 0.0)
            

    except:
        print("failed to rec")
        print(key)


async def run():
    """ Does Offboard control using velocity NED coordinates. """

    drone = System()
    await drone.connect(system_address="udp://:14540")

    print("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print(f"-- Connected to drone!")
            break

    print("Waiting for drone to have a global position estimate...")
    async for health in drone.telemetry.health():
        if health.is_global_position_ok and health.is_home_position_ok:
            print("-- Global position estimate OK")
            break

    print("-- Arming")
    await drone.action.arm()

    print("-- Setting initial setpoint")
    await drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, -0.5, 0.0))

    print("-- Starting offboard")
    try:
        await drone.offboard.start()
    except OffboardError as error:
        print(f"Starting offboard mode failed with error code: \
              {error._result.result}")
        print("-- Disarming")
        await drone.action.disarm()
        return
    
    listener = keyboard.Listener(
    on_press=on_press)
    listener.start()
    
    while (True):
        pass

    print("-- Stopping offboard")
    try:
        await drone.offboard.stop()
    except OffboardError as error:
        print(f"Stopping offboard mode failed with error code: \
              {error._result.result}")


if __name__ == "__main__":
    # Run the asyncio loop
    asyncio.run(run())