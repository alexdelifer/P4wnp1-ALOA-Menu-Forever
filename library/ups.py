import struct

def readVoltage(bus):
    # Function returns as float the voltage from the Raspi UPS Hat via the provided SMBus object.
    address = 0x36
    read = bus.read_word_data(address, 2)
    swapped = struct.unpack("<H", struct.pack(">H", read))[0]
    voltage = swapped * 1.25 / 1000 / 16
    return voltage


def readCapacity(bus):
    # This function returns as a float the remaining capacity of the battery connected to the Raspi UPS Hat via the provided SMBus object
    address = 0x36
    read = bus.read_word_data(address, 4)
    swapped = struct.unpack("<H", struct.pack(">H", read))[0]
    capacity = swapped / 256
    return capacity