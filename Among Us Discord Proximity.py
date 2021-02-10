import pymem
import time
import discord
import asyncio
from Player import Player

# Global definitions
pymem.logger.disabled = True
pymem.process.logger.disabled = True
intents = discord.Intents().all()
player_list_offsets = [0x012B89C8, 0x20, 0x2C, 0xE4]
individual_offset = 0xC0
boundary = 3
bot = discord.Client(intents=intents)
online_members = []
new_plr_objects = []
num_channels = [1, 1, 1, 1, 1, 1, 1]
plr_objects = []
text = voice = None
pm = None


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


def find_address_through_pointer(pymem_obj):
    # Uses the correct hack offsets for the pointer to get to the address
    address = 0
    try:
        game_assembly = pymem.process.module_from_name(pymem_obj.process_handle, "UnityPlayer.dll")
        address = game_assembly.lpBaseOfDll
        ptr = address
        for offset in player_list_offsets:
            address = ptr + offset
            if offset is not player_list_offsets[-1]:
                ptr = pymem_obj.read_int(address)
    except Exception as e:
        print(e)
        print("Error occured in pointers/offsets")
        input("Press any button to exit")
        exit(-3)
    return address


def get_player_address_list(address):
    # Finds the address of each player and returns list of the addresses
    player_address_list = [address]
    next_addr = address
    for i in range(9):
        next_addr += individual_offset
        player_address_list.append(next_addr)
    return player_address_list


async def validate_players(player_objects):
    for disc_plr in online_members:
        name = disc_plr.name
        await msg_send(f"Have {name} run around")
        time.sleep(5)
        validated = False
        while not validated:
            for key, player_obj in player_objects.items():
                try:
                    done = player_obj.validate(name)
                except AttributeError:
                    continue
                if done:
                    player_objects[key] = [disc_plr, player_obj]
                    validated = True
                    break
    time.sleep(3)
    del_keys = []
    for key, obj in player_objects.items():
        try:
            if not obj.validated:
                del_keys.append(key)
        except AttributeError:
            continue
    for key in del_keys:
        del player_objects[key]
    await msg_send("All players validated! Start the game!")
    return player_objects


def setup_players():
    # Controlls entire setup of instantiating players
    global pm
    pm = pymem.Pymem()
    attach_to_process(pm)

    address = find_address_through_pointer(pm)

    player_list = get_player_address_list(address)
    player_objects = {}
    for i, addr in enumerate(player_list):
        player_objects[i] = Player(addr, addr + 0x4, i, pm)
        # print(f"Player {i}: {player_objects[i].get_coords()}")
    print("Done setting up!")
    return player_objects


async def run_game(new_player_objects):
    just_moved = False
    # while True:
    #     for obj in new_player_objects.values():
    #         for second_obj in new_player_objects.values():
    #             if obj[1] is second_obj[1]:
    #                 break
    #             distance = obj[1].distance(second_obj[1])
    #             if distance < 2:
    #                 if obj[0].voice.channel != second_obj[0].voice.channel:
    #                     if int(obj[0].voice.channel.name) < int(second_obj[0].voice.channel.name):
    #                         await second_obj[0].move_to(obj[0].voice.channel)
    #                     else:
    #                         await obj[0].move_to(second_obj[0].voice.channel)
    #             else:
    #                 if obj[0].voice.channel == second_obj[0].voice.channel:
    #                     for channel in num_channels:
    #                         if not channel.members:
    #                             await second_obj[0].move_to(channel)
    #                             break
    while True:
        distance_table = []
        for i, obj in enumerate(new_player_objects.values()):
            for second_obj in list(new_player_objects.values())[i + 1:]:
                distance = obj[1].distance(second_obj[1])
                distance_table.append([obj[0], second_obj[0], distance])
        under_boundary = [entry for entry in distance_table if entry[2] < boundary]
        for dist_list in distance_table:
            if dist_list[2] < boundary:
                if dist_list[0].voice.channel != dist_list[1].voice.channel:
                    # if int(dist_list[0].voice.channel.name) < int(dist_list[1].voice.channel.name):
                    await dist_list[1].move_to(dist_list[0].voice.channel)
                    # else:
                    #     await dist_list[0].move_to(dist_list[1].voice.channel)
            else:
                if dist_list[0].voice.channel == dist_list[1].voice.channel:
                    for member in dist_list[0].voice.channel.members:
                        if member == dist_list[0] or member == dist_list[1]:
                            pass
                        else:
                            if under_boundary:
                                for entry in under_boundary:
                                    if entry[0] == dist_list[1] and entry[1] == member:
                                        break
                                    if entry[0] == member and entry[1] == dist_list[1]:
                                        break
                                else:
                                    continue
                                break

                            else:
                                for channel in num_channels:
                                    if not channel.members:
                                        await dist_list[1].move_to(channel)
                                        break
                    else:
                        for channel in num_channels:
                            if not channel.members:
                                await dist_list[1].move_to(channel)
                                break
        time.sleep(0.1)


@bot.event
async def on_ready():
    print("Ready!")
    global num_channels, text, voice, bot, online_members
    # server = bot.get_guild(789674745574064149)  # Test server
    server = bot.get_guild(771527740935372820)  # Tent 4
    # me = await server.fetch_member(247828844373999616)
    channels = server.channels
    for channel in channels:
        if channel.name == "proximity-commands":
            text = channel
        if channel.name in "1234567":
            num_channels.pop(int(channel.name) - 1)
            num_channels.insert(int(channel.name) - 1, channel)

    members = await server.fetch_members(limit=150).flatten()
    for member in members:
        if not member.bot:
            online_members.append(member)


@bot.event
async def on_message(msg):
    global plr_objects, text, online_members, new_plr_objects
    if msg.author.name == "LuckyZ":
        if msg.content == ".start":
            await text.send("Starting!")
            plr_objects = setup_players()
            await text.send(f"Out of {[mem.name for mem in online_members]}, who is not playing? Enter x to continue")

        elif msg.content == "x":
            new_plr_objects = await validate_players(plr_objects)
            await bot.wait_until_ready()
            await run_game(new_plr_objects)

        elif msg.content == ".continue":
            new_addr = find_address_through_pointer(pm)
            for obj in new_plr_objects:
                obj.reset_coordinates(new_addr, individual_offset)

        else:
            for mem in online_members:
                if msg.content in mem.name:
                    online_members.remove(mem)


async def msg_send(msg):
    await text.send(msg)


bot.run("TOKEN")
