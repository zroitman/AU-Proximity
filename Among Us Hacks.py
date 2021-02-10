import pymem
import time

pymem.logger.disabled = True
pymem.process.logger.disabled = True
hack_offsets = {
    1: [0x014A1634, 0x38, 0x50, 0x21C, 0x3C, 0x5C, 0xE4, 0x20],
    2: [0x014B20F0, 0x5C, 0x10, 0x34, 0x28],
    3: [0x01416E64, 0x8, 0xC8, 0x8, 0xA0, 0xC, 0x3C0],
}


def attach_to_process(pymem_obj):
    # Attaches to Among Us process and finds address of kill cooldown through pointers
    try:
        pymem_obj.open_process_from_name('Among Us.exe')

    except pymem.exception.ProcessNotFound:
        print("Could not find Among Us process, make sure the game is open")
        input("Press any button to exit")
        exit(-1)
    except pymem.exception.CouldNotOpenProcess:
        print("Could not open Among Us process for unknown reason")
        input("Press any button to exit")
        exit(-2)


def find_address_through_pointer(pymem_obj, choice):
    # Uses the correct hack offsets for the pointer to get to the address
    address = 0
    try:
        game_assembly = pymem.process.module_from_name(pymem_obj.process_handle, "GameAssembly.dll")
        address = game_assembly.lpBaseOfDll
        ptr = address
        hack = hack_offsets[choice]
        for offset in hack:
            address = ptr + offset
            if offset is not hack[-1]:
                ptr = pymem_obj.read_int(address)
    except Exception as e:
        print(e)
        print("Error occured in pointers/offsets")
        input("Press any button to exit")
        exit(-3)
    return address


def kill_cooldown(pymem_obj, address):
    # Ask user for cooldown value and write to memory
    print(f"Kill Cooldown variable found at {hex(address)}")
    time.sleep(1)

    valid = False
    value = 0
    while not valid:
        try:
            value = float(input("Enter the value you would like to set the cooldown to: "))
        except ValueError:
            pass
        valid = True
    pymem_obj.write_float(address, value)
    print("Success!")
    input("Press any button to exit")


def impostor(pymem_obj, address):
    # Ask user for impostor value and write to memory
    print(f"Impostor variable found at {hex(address)}")
    time.sleep(1)

    valid = False
    value = 0
    while not valid:
        try:
            value = int(input("Enter 0 for crewmate or 1 for impostor: "))
            if value in [0, 1]:
                valid = True
        except ValueError:
            pass

    pymem_obj.write_bytes(address, bytes([value]), 1)
    print("Success!")
    input("Press any button to exit")


def player_list(pymem_obj, address):
    pass


def main():
    # Main function to run program
    pm = pymem.Pymem()
    attach_to_process(pm)

    valid = False
    choice = 0
    while not valid:
        try:
            choice = int(input("Enter 1 for kill cooldown, 2 for impostor: "))
            if choice in [1, 2]:
                valid = True
            else:
                print("Please enter valid number")
        except ValueError:
            print("Please enter valid number")

    address = find_address_through_pointer(pm, choice)

    if choice == 1:
        kill_cooldown(pm, address)
    if choice == 2:
        impostor(pm, address)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        exit(1)
