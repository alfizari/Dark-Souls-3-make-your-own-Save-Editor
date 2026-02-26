from tkinter import filedialog, messagebox, simpledialog
import os, struct, json
import pc as PC

AOB_search= 'FF FF FF FF FF FF FF FF FF FF FF FF ??'
souls_distance = -219
hp_distance= -303
fp_distance= -291
stamina_distance= -275
MODE=None



# Stats offsets
stats_offsets_for_stats_tap = {
    "Level": -223,
    "Vigor": -267,
    "Attunement": -263,
    "Endurance": -259,
    "Vitality": -227,
    "Strength": -255,
    "Dexterity": -251,
    "Intelligence": -247,
    "Faith": -243,
    "Luck": -239,
    "Estus Flask Max (20 MAX)": -31,
    "Ashen Estus Flask Max (20 MAX)": -30,
}


bosses_offsets_for_bosses_tap = {
    "Iudex Gundyr": 23254,
    "Vordt of the Boreal Valley": 4054,
    "Curse-Rotted Greatwood": 6614,
    "Crystal Sage": 11736,
    "Abyss Watchers": 11734,
    "High Lord Wolnir": 20694, ##test
    "Oceiros, the Consumed King (pt1)": 4051,
    "Oceiros, the Consumed King (pt2)": 4058,
    "Champion Gundyr": 23251,
    "Dancer of the Boreal Valley": 4059,
    "Deacons of the Deep": 15574,
    "Old Demon King": 20691,
    "Pontiff Sulyvahn": 19416,
    "Aldrich, Devourer of Gods": 19414,
    "Dragonslayer Armour": 5334,
    "Yhorm the Giant": 21974,
    "Nameless King": 9176,
    "Twin Princes": 14291,
    "Soul of Cinder": 24534,
    "Champion's Gravetender (DLC)": 25815,
    "Father Ariandel and Sister Friede (DLC)": 25814,
    "Halflight, Spear of the Church (DLC)": 30934,
    "Darkeater Midir (DLC)": 30936,
    "Slave Knight Gael (DLC)": 32214,
    "Demon Prince (DLC)": 29654,
}

##For bonfire
bonfire_offsets_for_bonfire_tap = {
    "Activate Lord of Cinders in Firelink Shrine": 1288,
    "Cemetary of Ash": 23154,
    "High Wall of Lothric": 3953,
    "Undead Settlement": 6514,
    "Archdragon Peak": 9074,
    "Kiln of the First Flame": 24434,
    "Catacombs of Carthus": 20594,
    "Irithyll of the Boreal Valley": 19313,
    "Unlock Ariende's Room": 25789,
    "The Dreg Heap": 29554,
    "Irithyll Dungeon": 21874,
    "Road of Sacrifices": 11633,
    "Cathedral of the Deep": 15474,
    "Lothric Castle": 5234,
    "Grand Archives": 14194,
    "Painted World of Ariandel (DLC)": 25714,
    "The Ringed City (DLC)": 30834,
    "Filianore's Rest & Slave Knight Gael": 32114,
}


working_directory = os.path.dirname(os.path.abspath(__file__))
os.chdir(working_directory)

def load_json(file_name):
    file_path = os.path.join(working_directory, "json", file_name)
    with open(file_path, "r") as file:
        return json.load(file)
    
bosses_data=load_json('Bosses.json')
bonfire_data = load_json("bonfire.json")
goods_id=load_json('goods_magic.json')
rings_id=load_json('ring.json')
weapons_id=load_json('weapons.json')
armors_id=load_json('armor.json')
goods_id_bulk=load_json('goods_magic_bulk.json')
#Helpers
def find_hex_offset(section_data, hex_pattern):
    try:
        pattern_bytes = bytes.fromhex(hex_pattern)
        if pattern_bytes in section_data:
            return section_data.index(pattern_bytes)
        return None
    except ValueError as e:
        messagebox.showerror("Error", f"Failed to find hex pattern: {str(e)}")
        return None
    
def find_value_at_offset(section_data, offset, byte_size=4):
    try:
        value_bytes = section_data[offset:offset+byte_size]
        if len(value_bytes) == byte_size:
            return int.from_bytes(value_bytes, 'little')
    except IndexError:
        pass
    return None

def write_value_at_offset(data, offset, value, byte_size=4):
    value_bytes = value.to_bytes(byte_size, 'little')
    # Replace the bytes at the given offset with the new value
    return data[:offset] + value_bytes + data[offset+byte_size:]

def calculate_offset2(offset1, distance):
    return offset1 + distance
#AOB
def aob_to_pattern(aob: str):
    parts = aob.split()
    pattern = bytearray()
    mask = bytearray()

    for p in parts:
        if p == "??":
            pattern.append(0x00)
            mask.append(2)   # wildcard, must not be 0x00
        elif p == "!!":
            pattern.append(0x00)
            mask.append(0)   # wildcard, any byte including 0x00
        else:
            pattern.append(int(p, 16))
            mask.append(1)   # exact match

    return bytes(pattern), bytes(mask)


def aob_search(data: bytes, aob: str, min_offset: int = 0):
    pattern, mask = aob_to_pattern(aob)
    L = len(pattern)
    mv = memoryview(data)

    for i in range(min_offset, len(data) - L + 1):
        ok = True
        for j in range(L):
            if mask[j] == 1:
                if mv[i + j] != pattern[j]:
                    ok = False
                    break
            elif mask[j] == 2:
                if mv[i + j] == 0x00:
                    ok = False
                    break

        if ok:
            return i

    return None

def open_file():

    global MODE

    MODE=None

    file_path = filedialog.askopenfilename(title="Select userdata or DS30000.sl2 file", filetypes=[("All files", "*.*"), ("DAT files", "*.dat"), ("SL2 files", "*.sl2") ])
    if not file_path:
        return
    file_name = os.path.basename(file_path)
    print("Detected filename:", repr(file_name))
    if file_name.lower().startswith('userdata'):
        MODE= "ps4"
        print("Detected filename:", repr(file_name))
        print('PS4 file detected:', MODE, file_path)

        char_name=char_name_to_userdata0(file_path)

        print('char name list', char_name)
        if not char_name:
            messagebox.showerror("Error", "Can't find character name in the file. Make sure to select the correct file and that it is not corrupted.")
            return
        
        asked_char_name = simpledialog.askstring("Input", "Enter the character name you want to edit:")
        if not asked_char_name:
            messagebox.showerror("Error", "Character name cannot be empty.")
            return
        
        data, path = load_file_from_char_name(asked_char_name, char_name)

        return data, path

    elif (
            file_name == 'DS30000.sl2'
            or file_name.endswith('.co2')
            or file_name.endswith('.sl2')
            or file_name.endswith('.co')
            ):

        MODE= "PC" 
        PC.decrypt_ds2_sl2(file_path, 'decrypted_output')
        char_name=char_name_to_USERDATA_0('decrypted_output')
        print('char name list', char_name)
        if not char_name:
            messagebox.showerror("Error", "Can't find character name in the file. Make sure to select the correct file and that it is not corrupted.")
            return
        
        asked_char_name = simpledialog.askstring("Input", "Enter the character name you want to edit:")
        if not asked_char_name:
            messagebox.showerror("Error", "Character name cannot be empty.")
            return
        
        data, path = load_file_from_char_name(asked_char_name, char_name)

        return data, path

    else:
        messagebox.showerror("Error", "Please select a valid userdata (ps4) or DS30000.sl2 file. If your are on seamless, rename your file to DS30000.sl2 ")
        return


def char_name_to_userdata0(file_path):
    char_name = []

    with open(file_path, "rb") as f:
            data = f.read()
            data=bytearray(bytes.fromhex('00 00 0C 00')+ data)
            name=find_char_name(data)
            if name is None:
                messagebox.showerror('Error', "Can't find the character name on file")
                return
            char_name.append((name, file_path))

    return char_name
    
def load_file_from_char_name(asked_char_name, char_name):
    global MODE

    print('mode', MODE)


    for name, path in char_name:
        if name == asked_char_name:
            with open(path, "rb") as f:
                data = f.read()
                if MODE=='ps4':
                    data=bytearray(bytes.fromhex('00 00 0C 00') + data)

                return data, path

    messagebox.showerror('Error', "Can't find the file for the character name")
    return None, None

        

def char_name_to_USERDATA_0(folder_name):
    char_name = []

    split_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), folder_name)
    for i in range(10):

        file_path = os.path.join(split_dir, f"USERDATA_0{i}")
        with open(file_path, "rb") as f:
            data = f.read()
            name=find_char_name(data)
            if name is None:
                continue
            if folder_name == 'decrypted_output':
                char_name.append((name, file_path))

    return char_name
    ##print(char_name)


def find_char_name(data):

    end_offset_ga, ga_items, ga_armors, ga_weapons, ga_empty= gaprint(data)
    #print('end ', end_offset_ga)
    char_name_offset= end_offset_ga + 120

    max_chars = 16
    raw_name = data[char_name_offset:char_name_offset + max_chars * 2]
    char_name = raw_name.decode("utf-16-le", errors="ignore").rstrip("\x00")
    if char_name=='':
        return None


    ##print(char_name_offset, char_name)

    return char_name
#Ga parsing


def load_data(data):

    end_offset, ga_items, ga_armors, ga_weapons, ga_empty=gaprint(data)

    hex_pattern_fixed=end_offset + 0x13f

    current_char_name=find_char_name(data)
    #print('char name', current_char_name)

    current_souls_offset= hex_pattern_fixed + souls_distance
    current_souls= data[current_souls_offset:current_souls_offset+4] # 4 bytes
    #print('souls', current_souls)

    current_hp_offset= hex_pattern_fixed + hp_distance
    current_hp= data[current_hp_offset:current_hp_offset+4] # 4 bytes
    #print('hp', current_hp)

    current_fp_offset= hex_pattern_fixed + fp_distance
    current_fp= data[current_fp_offset:current_fp_offset+4]
    #print('fp', current_fp)

    current_st_offset= hex_pattern_fixed + stamina_distance
    current_st=data[current_st_offset: current_st_offset+4]
    #print('st', current_st)

    save_info = parse_save(data)

    steam_id_offset = save_info["steam_id_offset_true"]
    current_ng_offset = save_info["new_game_plus"]
    current_ng_value=data[current_ng_offset: current_ng_offset+1] #1 byte
    #print('ng', current_ng_value)

    steam_id_value, steam_offset = check_steam_id(data)

    if MODE == 'PC' and steam_id_value == 0:
        print('steam id error')


    for stat, distance in stats_offsets_for_stats_tap.items():
        stat_offset = hex_pattern_fixed + distance
        

        byte_size = 2
        
        current_stat_value = int.from_bytes(
            data[stat_offset:stat_offset + byte_size],
            byteorder="little"
        )
        
        print(f"{stat}: {current_stat_value}")

    

def change_name(data, new_name):

    end_offset_ga, ga_items, ga_armors, ga_weapons, ga_empty= gaprint(data)
    name_offset = end_offset_ga + 120
    byte_size = 32

    # Encode
    name_bytes = new_name.encode("utf-16-le")

    # Truncate if too long
    name_bytes = name_bytes[:byte_size]

    # Pad if too short
    name_bytes += b'\x00' * (byte_size - len(name_bytes))

    # Replace bytes
    data = data[:name_offset] + name_bytes + data[name_offset + byte_size:]

    return data

def change_souls(data, souls):
    end_offset, ga_items, ga_armors, ga_weapons, ga_empty = gaprint(data)

    hex_pattern_fixed = end_offset + 0x13F
    current_souls_offset = hex_pattern_fixed + souls_distance

    souls = max(0, min(souls, 0xFFFFFFFF))

    souls_bytes = souls.to_bytes(4, byteorder="little", signed=False)

    # Replace bytes
    data = (
        data[:current_souls_offset] +
        souls_bytes +
        data[current_souls_offset + 4:]
    )

    return data


def change_hp(data, health):
    end_offset, ga_items, ga_armors, ga_weapons, ga_empty = gaprint(data)

    hex_pattern_fixed = end_offset + 0x13F
    current_hp_offset = hex_pattern_fixed + hp_distance

    health = max(0, min(health, 0xFFFFFFFF))

    health_bytes = health.to_bytes(4, byteorder="little", signed=False)

    # Replace bytes
    data = (
        data[:current_hp_offset] +
        health_bytes +
        data[current_hp_offset + 4:]
    )

    return data


def change_st(data, st):
    end_offset, ga_items, ga_armors, ga_weapons, ga_empty = gaprint(data)

    hex_pattern_fixed = end_offset + 0x13F
    current_st_offset = hex_pattern_fixed + stamina_distance

    st = max(0, min(st, 0xFFFFFFFF))

    st_bytes = st.to_bytes(4, byteorder="little", signed=False)

    # Replace bytes
    data = (
        data[:current_st_offset] +
        st_bytes +
        data[current_st_offset + 4:]
    )

    return data

def change_fp(data, fp):
    end_offset, ga_items, ga_armors, ga_weapons, ga_empty = gaprint(data)

    hex_pattern_fixed = end_offset + 0x13F
    current_fp_offset = hex_pattern_fixed + fp_distance

    fp = max(0, min(fp, 0xFFFFFFFF))

    fp_bytes = fp.to_bytes(4, byteorder="little", signed=False)

    # Replace bytes
    data = (
        data[:current_fp_offset] +
        fp_bytes +
        data[current_fp_offset + 4:]
    )

    return data


def change_stats(data, stat_name, stat_value):

    end_offset, ga_items, ga_armors, ga_weapons, ga_empty = gaprint(data)
    hex_pattern_fixed = end_offset + 0x13F

    for stat, distance in stats_offsets_for_stats_tap.items():
        if stat_name == stat:

            stat_offset = hex_pattern_fixed + distance

            byte_size = 2

            stat_bytes = stat_value.to_bytes(byte_size, byteorder="little")

            # Replace bytes
            data = (
                data[:stat_offset] +
                stat_bytes +
                data[stat_offset + byte_size:]
            )

            break

    return data




    
    


ITEM_TYPE_EMPTY = 0x00000000
ITEM_TYPE_WEAPON = 0x80000000
ITEM_TYPE_ARMOR  = 0x90000000

class Item:

    BASE_SIZE= 8

    def __init__(self, gaitem_handle, item_id, offset , size=BASE_SIZE):

        self.gaitem_handle= gaitem_handle
        self.item_id= item_id
        self.size= size
        self.offset= offset

    @classmethod
    def from_bytes(cls, data_type, offset= 0 ):

        gaitem_handle, item_id= struct.unpack_from("<II", data_type, offset)
        type_bits= gaitem_handle & 0xF0000000
        extra = {}
        cursor = offset + cls.BASE_SIZE
        size = cls.BASE_SIZE

        if gaitem_handle != 0:
            if type_bits == ITEM_TYPE_WEAPON:
                cursor += 52

                size = cursor - offset
            elif type_bits == ITEM_TYPE_ARMOR:

                cursor += 52
                size= cursor-offset


        return cls(gaitem_handle, item_id, offset, size)
    


def parse_items(data_type, start_offset, slots=6144):
    items = []
    offset = start_offset

    for _ in range(slots):
        item = Item.from_bytes(data_type, offset)
        items.append(item)
        offset += item.size


    return items, offset


def gaprint(data_type, slots= 6144):

    save_data=data_type
    ga_items=[]
    ga_weapons=[]
    ga_armors=[]
    ga_empty=[]

    start_offset = 0x70

    items , end_offset= parse_items(save_data, start_offset, slots)

    for item in items:
        type_bits = item.gaitem_handle & 0xF0000000
        ga_items.append((item.gaitem_handle, item.item_id, item.offset))
        if type_bits == ITEM_TYPE_WEAPON:
            ga_weapons.append((item.gaitem_handle, item.item_id, item.offset))
        elif type_bits == ITEM_TYPE_ARMOR:
            ga_armors.append((item.gaitem_handle, item.item_id, item.offset))
        elif type_bits == ITEM_TYPE_EMPTY:
            ga_empty.append((item.gaitem_handle, item.item_id, item.offset)) 

    ##print(ga_items[-1][2])
    ##print(len(ga_items))

    return end_offset, ga_items, ga_armors, ga_weapons, ga_empty

def parse_save(data):

    end_offset, ga_items, ga_armors, ga_weapons, ga_empty= gaprint(data)
    ##print('ga end', hex(end_offset))

    magic_start= end_offset + 0x13F
    ##print("magic start", hex(magic_start))

    inventory_start= magic_start + 0x1dd
    #print('inventory start', hex(inventory_start))

    inventory_end= inventory_start + 0x8808
    #print('inventory end', hex(inventory_end))

    above_storage_counter=inventory_end + 0x11c
    ##print('above storage counter', hex(above_storage_counter))

    above_storage_counter_size= struct.unpack_from('<I', data, above_storage_counter)[0]
    ##print('above storage counter', hex(above_storage_counter_size))

    table_1_end= above_storage_counter + 4 + (above_storage_counter_size * 8)
    ##print('table 1 end', hex(table_1_end))

    face_data_maybe= table_1_end + 0x18c
    ##print('face data maybe', hex(face_data_maybe))

    storage_box_start= face_data_maybe + 0x4
    ##print('storage box start', hex(storage_box_start))

    storage_box_end= storage_box_start + 0x8800
    ##print('storage_box_end', hex(storage_box_end))

    gesture_start= storage_box_end +0xc
    ##print('gesture start', hex(gesture_start))

    gesture_end= gesture_start + 0xa4
    ##print('gesture end', hex(gesture_end))

    table_2_size= struct.unpack_from('<I', data, gesture_end)[0]
    ##print('table 2 size', table_2_size)

    table_2_end= gesture_end + 4 + (table_2_size*4)
    ##print('table 2 end', hex(table_2_end))

    new_game_plus= table_2_end + 0x92
    ##print('ng+ offset', hex(new_game_plus))

    new_game_plus_value=struct.unpack_from('<H',data, new_game_plus)[0]
    ##print('ng+ =', new_game_plus_value)

    event_flag_start= new_game_plus + 0xbCC
    #print('event flag start', hex(event_flag_start))

    event_flag_end= event_flag_start + 0x33e5e
    ##print('even flag end maybe', hex(event_flag_end))

    block_1_size=struct.unpack_from('<I',data, event_flag_end)[0]
    ##print('block 1 size', block_1_size)

    block_1_end= event_flag_end + 4 + (block_1_size)
    ##print('block 1 end', hex(block_1_end))

    block_2_size=struct.unpack_from('<I',data, block_1_end)[0]
    ##print('block 2 size', block_2_size)

    block_2_end= block_1_end + 4 + (block_2_size)
    ##print('block 1 end', hex(block_2_end))

    block_3_size=struct.unpack_from('<I',data, block_2_end)[0]
    ##print('block 3 size', block_3_size)

    block_3_end= block_2_end + 4 + (block_3_size)
    ##print('block 3 end', hex(block_3_end))

    block_4_end=block_3_end + 0xe
    ##print('block 4 end', hex(block_4_end))

    block_5_start= block_4_end + 0x6a
    ##print('block 5 start', hex(block_5_start))

    block_5_size= struct.unpack_from('<I',data, block_5_start)[0]
    ##print('block 5 size', block_5_size)

    block_5_end= block_5_start + 4 + block_5_size
    ##print('block 5 end', hex(block_5_end))

    block_6_start= block_5_end + 4
    ##print('block 6 start', hex(block_6_start))

    block_6_size= struct.unpack_from('<I',data, block_6_start)[0]
    ##print('block 6 size', block_6_size)

    block_6_end= block_6_start + 4 + block_6_size
    ##print('block 6 end', hex(block_6_end))
    # no idea here

    steam_id=aob_search(data[block_6_end:], AOB_search)
    if MODE=='PC' and steam_id is None:
        print('Cannot find steam id')

    steam_id_offset= steam_id + block_6_end


    steam_id_offset_true= steam_id_offset + 0x1c
    #print('steam id offset', hex(steam_id_offset_true))

    return {
    "steam_id_offset_true": steam_id_offset_true,
    "new_game_plus": new_game_plus,
    "event_flag_start": event_flag_start,
    "inventory_start": inventory_start,
    "storage_box_start": storage_box_start,
    "storage_box_end" : storage_box_end
    }

def check_steam_id(data):

    if data is None:
        print('err')

    steam_offset = parse_save(data)["steam_id_offset_true"]
    if steam_offset is None:
        return None

    steam_id_value = struct.unpack_from('<Q', data, steam_offset)[0]
    steam=int.to_bytes(steam_id_value, 8, 'little')
    #print(steam.hex())
    return steam, steam_offset



def get_boss_status(data):
    global bosses_data
    bosses_status = {}

    

    start_offset = parse_save(data)["event_flag_start"]

    start_offset_true=start_offset-0x12

    if start_offset_true is not None:
        for boss, defeat_hex in bosses_data.items():
            defeat_value = int(defeat_hex, 16)  # Convert hex string to integer for comparison
            boss_distance = bosses_offsets_for_bosses_tap.get(boss)  # Retrieve distance for boss
            
            if boss_distance is not None:
                # Calculate the offset based on fixed offset and boss distance
                boss_offset = calculate_offset2(start_offset_true, boss_distance)
                
                # Read only 1 byte at the boss offset
                boss_value = struct.unpack_from('<b', data, boss_offset)[0]
                
                # Determine if the boss is defeated or alive
                bosses_status[boss] = "Defeated" if boss_value == defeat_value else "Alive"
            else:
                print(f"Warning: Offset for boss '{boss}' not found.")
    #print('bosses', bosses_status)           
    return bosses_status

def change_boss_status(data, boss_name, new_status):
    global bosses_data

    offset1_old = parse_save(data)["event_flag_start"]
    offset1=offset1_old-0x12

    boss_distance = bosses_offsets_for_bosses_tap[boss_name]
    boss_offset = calculate_offset2(offset1, boss_distance)
    defeat_value = int(bosses_data[boss_name], 16)

    # Set the value to 1 byte: defeat value for "Defeated" or 0 for "Alive"
    value = defeat_value if new_status == "Defeated" else 0  # 0 for alive
    struct.pack_into('<b', data, boss_offset, value)

    return data

def get_bonfire_status(data):
    global bonfire_data
    bonfire_status = {}
    offset1_old = parse_save(data)["event_flag_start"]
    offset1=offset1_old-0x12
    if offset1 is not None:
        for bonfire, bonfire_hex in bonfire_data.items():
            bonfire_value = int(bonfire_hex, 16)  # Convert hex string to integer
            bonfire_distance = bonfire_offsets_for_bonfire_tap.get(bonfire)  # Retrieve offset distance
            
            if bonfire_distance is not None:
                # Calculate the offset based on fixed offset and bonfire distance
                bonfire_offset = calculate_offset2(offset1, bonfire_distance)
                
                # Read the value (try 1 byte first, then 2 bytes)
                read_value = struct.unpack_from('<b', data, bonfire_offset)[0]
                if read_value != bonfire_value:
                    read_value = struct.unpack_from('<h', data, bonfire_offset)[0] #2 bytes

                # Determine bonfire status
                bonfire_status[bonfire] = "Unlocked" if read_value == bonfire_value else "Locked"
            else:
                print(f"Warning: Offset for bonfire '{bonfire}' not found.")
    #print('bonfire', bonfire_status)
    return bonfire_status

def change_bonfire_status(data, bonfire_name, bonfire_status):
    global bonfire_data

    # Make sure data is mutable
    if isinstance(data, bytes):
        data = bytearray(data)

    offset1_old = parse_save(data)["event_flag_start"]
    offset1 = offset1_old - 0x12

    if offset1 is not None and bonfire_name in bonfire_data:

        bonfire_distance = bonfire_offsets_for_bonfire_tap[bonfire_name]
        bonfire_offset = calculate_offset2(offset1, bonfire_distance)

        unlock_value = int(bonfire_data[bonfire_name], 16)

        # Choose correct struct format
        if unlock_value <= 0xFF:
            fmt = '<B'  
        else:
            fmt = '<H'   

        value = unlock_value if bonfire_status == "Unlocked" else 0


        struct.pack_into(fmt, data, bonfire_offset, value)

    return data


# iNVENTORY section

ITEM_TYPE_EMPTY = 0x00000000
ITEM_TYPE_WEAPON = 0x80000000
ITEM_TYPE_ARMOR  = 0x90000000
ITEM_TYPE_GOOD = 0XB0000000
ITEM_TYPE_RINGS= 0XA0000000 

class INVENTORY:
    BASE_SIZE = 16

    def __init__(self, gaitem_handle, item_id, quantity, index, offset):
        self.gaitem_handle = gaitem_handle 
        self.item_id = item_id
        self.quantity = quantity
        self.index = index
        self.offset = offset
        self.size = self.BASE_SIZE

    @classmethod
    def from_bytes(cls, data, offset=0):
        gaitem_handle, item_id,quantity, index = struct.unpack_from("<IIII", data, offset)
        return cls(gaitem_handle,item_id, quantity, index, offset)




def parse_inventory(data, start_offset, end_offset):
    inventory_item = []
    offset = start_offset

    while offset < end_offset:
        item = INVENTORY.from_bytes(data, offset)
        inventory_item.append(item)
        offset += item.size  

    return inventory_item

def inventoryprint(data):
    
    inventory_items=[]
    weapons = []
    armors = []
    goods = []
    rings = []
    empty=[]

    start_offset = parse_save(data)["inventory_start"]

    end_offset = start_offset +0x7800


    items = parse_inventory(data, start_offset, end_offset)

    for item in items:
        type_bits = item.gaitem_handle & 0xF0000000
        inventory_items.append((item.gaitem_handle, item.item_id, item.quantity, item.index, item.offset))

        if type_bits == ITEM_TYPE_WEAPON:
            weapons.append((item.gaitem_handle, item.item_id, item.quantity, item.index, item.offset))
        elif type_bits == ITEM_TYPE_ARMOR:
            armors.append((item.gaitem_handle, item.item_id, item.quantity, item.index, item.offset))
        elif type_bits == ITEM_TYPE_GOOD:
            goods.append((item.gaitem_handle, item.item_id, item.quantity, item.index, item.offset))
        elif type_bits == ITEM_TYPE_RINGS:
            rings.append((item.gaitem_handle, item.item_id, item.quantity, item.index, item.offset))
        elif type_bits == ITEM_TYPE_EMPTY:
            empty.append((item.gaitem_handle, item.item_id, item.quantity, item.index, item.offset))
    ##print('inventory items', inventory_items)

    return inventory_items, weapons, armors,goods, rings, empty


def increment_inventory_counter(data):

    # Ensure mutable buffer
    if isinstance(data, bytes):
        data = bytearray(data)

    inventory_start = parse_save(data)["inventory_start"]

    first_counter_offset = inventory_start - 4
    snd_counter_offset = inventory_start + 0x89E5 - 0x1dd

    first_counter = struct.unpack_from('<h', data, first_counter_offset)[0]
    snd_counter = struct.unpack_from('<h', data, snd_counter_offset)[0]

    first_counter += 1
    snd_counter += 1

    struct.pack_into('<h', data, first_counter_offset, first_counter)
    struct.pack_into('<h', data, snd_counter_offset, snd_counter)

    return data

def add_goods_rings(data, item_name, new_quantity, stack=False, item_type='goods'):

    original_data = data  # Save original before any modifications

    inventory_items, weapons, armors,goods, rings, empty=inventoryprint(data)

    #we load item id from json

    if item_type=='goods':

        item_id = goods_id.get(item_name)

        if not item_id:
            messagebox.showerror("Error", f"Item '{item_name}' not found in goods_magic.json.")
            return data
        
    elif item_type=='rings':

        item_id = rings_id.get(item_name)
        
        if not item_id:
            messagebox.showerror("Error", f"Item '{item_name}' not found in ring.json.")
            return data

    item_id_bytes = bytes.fromhex(item_id)
    if len(item_id_bytes) != 4:
        messagebox.showerror("Error", f"Invalid ID for '{item_name}'. ID must be exactly 4 bytes.")
        return data
    
    max_quantity = 99
    new_quantity = min(new_quantity, max_quantity)  # Ensure quantity does not exceed max

    #check if the item already exists 

    item_id_int= int.from_bytes(item_id_bytes, 'little')
    #print('item id int', item_id_int)
    #print('item id bytes', item_id_bytes.hex())

    if item_type=='goods' and stack == False:
        #print('stack false')
        for i, (gaitem_handle, item_id, quantity, index, offset) in enumerate(goods):
                if item_id_int == item_id:

                    quantity_offset = offset + 8
                    data = (
                        data[:quantity_offset] 
                        + new_quantity.to_bytes(4, 'little') 
                        + data[quantity_offset+4:]
                    )
                    #print('quantity offset',quantity_offset )
                    # update inventory_items to reflect the new quantity
                    inventory_items[i] = (gaitem_handle,item_id, new_quantity, index, offset)

                    #print('item_found')
                    return data
                #to be continued
    
    first_empty_slot=empty[0][4]
    #print('empty slot count', len(empty))

    
    
    #print('first empty slot', hex(first_empty_slot))

    highest_index = [item[3] & 0x00000Fff for item in inventory_items]
    ##print(highest_index[:10])

    highest_index = [x for x in highest_index if x != 0]
    ##print('highest index', highest_index)
    highest_index = max(highest_index) if highest_index else 0
    #print('highest index', hex(highest_index))
    
    highest_index+=1
    #print('highest index', hex(highest_index))

    highest_index=highest_index.to_bytes(2, 'little')
    #print('highest index',highest_index.hex())

    new_quantity=new_quantity.to_bytes(4, 'little') 
    #we make new slot to be placed on an empty slot

    random_byte = os.urandom(1)[0]
    ##print('rando', random_byte)
    if item_type=='goods':
        new_slot= bytearray.fromhex('C8 6B 35 B0 C8 6B 35 40 01 00 00 00 7D C1 CF 1F')
    elif item_type=='rings':
        new_slot= bytearray.fromhex('C8 6B 35 A0 C8 6B 35 40 01 00 00 00 7D C1 CF 1F')
    #4 bytes: item_id[:3] first 3 bytes of the item id
    #4 bytes: full item id
    #4 bytes: quantity
    #4 bytes: index. first byte and the lowest nibble if the 2nd byte, the rest is sorting??
    new_slot[:3]=item_id_bytes[:3]
    new_slot[4:8]=item_id_bytes
    new_slot[8:12]=new_quantity
    new_slot[12]=highest_index[0]
    new_slot[13] = (random_byte & 0xF0) | (highest_index[1] & 0x0F) #keep the highest nibble the same but change the lowest
    #print(new_slot.hex())

    if len(empty) <2:
        
        data, STORAGE_FULL_FLAG= add_item_to_storage(data, item_name)
        return data, STORAGE_FULL_FLAG

    # Write the new slot to the data at the first empty slot offset
    data = (
        data[:first_empty_slot] 
        + new_slot 
        + data[first_empty_slot + 16:]
    )

    data=increment_inventory_counter(data)

    return data

def bulk_add_goods_rings(data, item_type):
    if item_type == 'goods':
        source_dict = goods_id

        # show the user the categories and let them check which one to bulk add or what collection of them
        # Define categories
        categories = {
            "Consumables": list(goods_id_bulk.items())[:51],
            "Covenant": list(goods_id_bulk.items())[51:57],
            "Souls": list(goods_id_bulk.items())[57:78],
            "Boss Souls": list(goods_id_bulk.items())[78:101],
            "Upgrade Materials (SLABS not included)": list(goods_id_bulk.items())[101:106],
            "Gems": list(goods_id_bulk.items())[106:121],
            "Coals": list(goods_id_bulk.items())[121:125],
            "Ashes/Bone": list(goods_id_bulk.items())[125:144],
            "Tome/Scroll": list(goods_id_bulk.items())[144:157],
            "Magic": list(goods_id_bulk.items())[157:268],
            
        }

        category_quantity_limits = { #others are 99
            "Coals": 1,
            "Ashes/Bone": 1,
            "Tome/Scroll": 1,
            "Magic": 1, 

        }
    elif item_type == 'rings': # quantity 1
        source_dict = rings_id
        quantity=1
    else:
        return data

    for count, (item_name, item_id) in enumerate(source_dict.items(), start=1):

        data, no_more_slots = add_goods_rings(data, item_name, quantity,  stack=False, item_type=item_type)

        if no_more_slots:
            print(f"No more slots available for {item_type}: {item_name}")
            break

        if item_type == 'weapon' and count == 310:
            print('last weapon', item_name)
            break

    return data



def add_weapon_armor(data, item_name, item_type='weapon'):
    original_data = bytes(data)  # Save original before any modifications
    data = bytearray(data)
    NO_MORE_SLOT_FLAG=False

    try:
        if item_type=='weapon':
            item_id = weapons_id.get(item_name)
            if not item_id:
                messagebox.showerror("Error", f"Item '{item_name}' not found in weapon.json.")
                NO_MORE_SLOT_FLAG=True
                return original_data, NO_MORE_SLOT_FLAG
            
        elif item_type=='armor':
            item_id = armors_id.get(item_name)
            if not item_id:
                messagebox.showerror("Error", f"Item '{item_name}' not found in armor.json.")
                NO_MORE_SLOT_FLAG=True
                return original_data, NO_MORE_SLOT_FLAG

        item_id_bytes = bytes.fromhex(item_id)
        if len(item_id_bytes) != 4:
            messagebox.showerror("Error", f"Invalid ID for '{item_name}'. ID must be exactly 4 bytes.")
            NO_MORE_SLOT_FLAG=True
            return original_data, NO_MORE_SLOT_FLAG
        
        end_offset, ga_items, ga_armors, ga_weapons, ga_empty= gaprint(data)

        if len(ga_empty) <5:
            print('No ga empty slot')
            NO_MORE_SLOT_FLAG=True
            return original_data, NO_MORE_SLOT_FLAG
        
        ga_items_index=[item[0] & 0x0000FFFF for item in ga_items if item[0] != 0]
        ga_items_index =max(ga_items_index) if ga_items_index else 0

        first_empty = min(ga_empty, key=lambda x: x[2])
        _, _, ga_empty_slot = first_empty

        ga_items_index+=1
        ga_highest_index=ga_items_index.to_bytes(2, 'little')

        if item_type=='weapon':
            ga_slot=bytearray.fromhex('5D 09 80 80 A0 DB 5B 00 4B 00 00 00 00 00 00 00 01 00 00 00 00 00 00 80 00 00 00 00 00 00 00 80 00 00 00 00 00 00 00 80 00 00 00 00 00 00 00 80 00 00 00 00 00 00 00 80 00 00 00 00')
        elif item_type=='armor':
            ga_slot=bytearray.fromhex('76 06 81 90 58 5E 57 11 68 01 00 00 00 00 00 00 01 00 00 00 00 00 00 80 00 00 00 00 00 00 00 80 00 00 00 00 00 00 00 80 00 00 00 00 00 00 00 80 00 00 00 00 00 00 00 80 00 00 00 00')

        ga_slot[:2]=ga_highest_index
        ga_slot[4:8]=item_id_bytes

        data=(
            data[:ga_empty_slot] 
            + ga_slot 
            + data[ga_empty_slot:]
        )

        end_offset, ga_items, ga_armors, ga_weapons, ga_empty= gaprint(data, slots=6145)

        if len(ga_empty) <5:
            print('No ga empty slot')
            NO_MORE_SLOT_FLAG=True
            return original_data, NO_MORE_SLOT_FLAG
        
        first_empty_del = min(ga_empty, key=lambda x: x[2])
        _, _, ga_empty_slot = first_empty_del

        data = (
            data[:ga_empty_slot] 
            + data[ga_empty_slot + 0x8:] 
        )

        inventory_items, weapons, armors, goods, rings, empty=inventoryprint(data)

        first_empty_slot=empty[0][4]

        

        highest_index = [item[3] & 0x00000Fff for item in inventory_items]
        highest_index = [x for x in highest_index if x != 0]
        highest_index = max(highest_index) if highest_index else 0
        
        highest_index+=1
        highest_index=highest_index.to_bytes(2, 'little')

        random_byte = os.urandom(1)[0]

        if item_type=='weapon':
            new_slot= bytearray.fromhex('19 0A 80 80 B0 AD 01 00 01 00 00 00 82 00 18 FB')
        elif item_type=='armor':
            new_slot= bytearray.fromhex('94 08 80 90 80 F9 37 13 01 00 00 00 FC 00 65 FE')

        new_slot[:2]=ga_highest_index
        new_slot[4:8]=item_id_bytes
        new_slot[12]=highest_index[0]
        new_slot[13] = (random_byte & 0xF0) | (highest_index[1] & 0x0F)


        if len(empty) <2:
            print('No empty slot, adding item to storage instead')
            data, STORAGE_FULL_FLAG = add_item_to_storage(data, new_slot)
            return data, STORAGE_FULL_FLAG

        if first_empty_slot==None:
            print('no more slots found')
            data, STORAGE_FULL_FLAG = add_item_to_storage(data, new_slot)
            return data, STORAGE_FULL_FLAG

        data = (
            data[:first_empty_slot] 
            + new_slot 
            + data[first_empty_slot + 16:]
        )

        data=increment_inventory_counter(data)

        steam_id_offset_true = parse_save(data)["steam_id_offset_true"]

        delete_size = 0x34
        end_cutoff = 0xD

        delete_start = len(data) - delete_size - end_cutoff
        delete_end = len(data) - end_cutoff

        if delete_start < steam_id_offset_true + 50:
            print("Deletion skipped: too close to Steam ID offset")
            NO_MORE_SLOT_FLAG=True
            return original_data, NO_MORE_SLOT_FLAG
        else:
            data = data[:delete_start] + data[delete_end:]

        return data, STORAGE_FULL_FLAG

    except Exception as e:
        print(f"Error in add_weapon_armor: {e}")
        STORAGE_FULL_FLAG=True
        return original_data, STORAGE_FULL_FLAG


def save_file(data, data_path):
    global MODE


    print('MODE', MODE)

    if MODE=='PC':
        #print('encrypting for PC', MODE, data_path)
        with open(data_path, 'wb') as file:
            file.write(data)

        out_path=filedialog.asksaveasfilename(title='Save your PC save', initialfile='DS30000.sl2')
        PC.encrypt_modified_files(out_path)

    elif MODE=='ps4':
        file_name=os.path.basename(data_path)
        data=bytearray(data[0x4:])
        out_path=filedialog.asksaveasfilename(title='Save your PS4 save', initialfile=file_name)
        with open(out_path, 'wb') as file:
            file.write(data)



    return

def bulk_add_weapon_or_armor(data, item_type):

    if item_type == 'weapon':
        source_dict = weapons_id
    elif item_type == 'armor':
        source_dict = armors_id
    else:
        return data

    for count, (item_name, item_id) in enumerate(source_dict.items(), start=1):

        data, no_more_slots = add_weapon_armor(data, item_name, item_type)

        if no_more_slots:
            print(f"No more slots available for {item_type}: {item_name}")
            break

        if item_type == 'weapon' and count == 310:
            print('last weapon', item_name)
            break

    return data


def storageprint(data, start_offset, end_offset):
    
    storage_items=[]
    weapons = []
    armors = []
    goods = []
    rings = []
    empty=[]



    items = parse_inventory(data, start_offset, end_offset)

    for item in items:
        type_bits = item.gaitem_handle & 0xF0000000
        storage_items.append((item.gaitem_handle, item.item_id, item.quantity, item.index, item.offset))

        if type_bits == ITEM_TYPE_WEAPON:
            weapons.append((item.gaitem_handle, item.item_id, item.quantity, item.index, item.offset))
        elif type_bits == ITEM_TYPE_ARMOR:
            armors.append((item.gaitem_handle, item.item_id, item.quantity, item.index, item.offset))
        elif type_bits == ITEM_TYPE_GOOD:
            goods.append((item.gaitem_handle, item.item_id, item.quantity, item.index, item.offset))
        elif type_bits == ITEM_TYPE_RINGS:
            rings.append((item.gaitem_handle, item.item_id, item.quantity, item.index, item.offset))
        elif type_bits == ITEM_TYPE_EMPTY:
            empty.append((item.gaitem_handle, item.item_id, item.quantity, item.index, item.offset))
    ##print('inventory items', inventory_items)

    return storage_items, weapons, armors,goods, rings, empty

def parse_storage(data):


    save_info=parse_save(data)

    storage_offset_start=save_info["storage_box_start"]
    #storage_offset_end=save_info["storage_box_end"]
    storage_offset_end= storage_offset_start + 0x7800

    storage_items, weapons, armors,goods, rings, empty=storageprint(data, storage_offset_start, storage_offset_end)

    #When displaying each item type, the quantity for goods is the only one that matters
    
    #print('storage', rings)

    return goods

def add_item_to_storage(data, item_slot):

    STORAGE_FULL_FLAG=False

    orginal_data=data

    save_info=parse_save(data)

    storage_offset_start=save_info["storage_box_start"]
    #storage_offset_end=save_info["storage_box_end"]
    storage_offset_end= storage_offset_start + 0x7800

    storage_items, weapons, armors,goods, rings, empty=storageprint(data, storage_offset_start, storage_offset_end)

    #find first empty slot

    if len(empty) < 2:

        print(' not storage slots')
        STORAGE_FULL_FLAG=True
        return orginal_data, STORAGE_FULL_FLAG
    
    increment_storage_counter(data, storage_offset_start)
    
    _,_,_,_, first_empty_offset= empty[0]

    data=(
        data[:first_empty_offset] 
        + item_slot 
        + data[first_empty_offset + 16:]
    )

    return data, STORAGE_FULL_FLAG
    


def increment_storage_counter(data, storage_offset_start):

    counter_offset=storage_offset_start-4

    counter=struct.unpack_from('<I', data, counter_offset)[0]

    counter +=1

    struct.pack_into('<I', data, counter_offset, counter)

    return data


def modify_goods_storage_quantity(data, item_name, quantity):

    goods_list=parse_storage(data)



    item_id = goods_id.get(item_name)

    if not item_id:
        messagebox.showerror("Error", f"Item '{item_name}' not found in goods_magic.json.")
        return data


    item_id_bytes = bytes.fromhex(item_id)
    if len(item_id_bytes) != 4:
        messagebox.showerror("Error", f"Invalid ID for '{item_name}'. ID must be exactly 4 bytes.")
        return data
    
    max_quantity = 666
    new_quantity = min(new_quantity, max_quantity) 

    #check if the item already exists 

    item_id_int= int.from_bytes(item_id_bytes, 'little')


    for _,item,_,_,item_offset in goods_list:
        if item==item_id_int:

            quantity_offset = item_offset + 8
            data = (
                data[:quantity_offset] 
                + new_quantity.to_bytes(4, 'little') 
                + data[quantity_offset+4:]
            )
            #update the list
            parse_storage(data)

            
    return data



def open_file_import():

    file_path = filedialog.askopenfilename(title="Select userdata or DS30000.sl2 file", filetypes=[("All files", "*.*"), ("DAT files", "*.dat"), ("SL2 files", "*.sl2") ])
    if not file_path:
        return
    file_name = os.path.basename(file_path)
    print("Detected filename:", repr(file_name))
    if file_name.lower().startswith('userdata'):
        MODE= "ps4"
        print("Detected filename:", repr(file_name))
        print('PS4 file detected:', MODE, file_path)

        char_name=char_name_to_userdata0(file_path)

        print('char name list', char_name)
        if not char_name:
            messagebox.showerror("Error", "Can't find character name in the file. Make sure to select the correct file and that it is not corrupted.")
            return
        
        asked_char_name = simpledialog.askstring("Input", "Enter the character name you want to edit:")
        if not asked_char_name:
            messagebox.showerror("Error", "Character name cannot be empty.")
            return
        
        import_data, import_path = load_file_from_char_name(asked_char_name, char_name)

        return import_data, import_path

    elif (
            file_name == 'DS30000.sl2'
            or file_name.endswith('.co2')
            or file_name.endswith('.sl2')
            or file_name.endswith('.co')
            ):

        MODE= "PC" 
        PC.decrypt_ds2_sl2(file_path, 'decrypted_import')
        char_name=char_name_to_USERDATA_0('decrypted_import')
        print('char name list', char_name)
        if not char_name:
            messagebox.showerror("Error", "Can't find character name in the file. Make sure to select the correct file and that it is not corrupted.")
            return
        
        asked_char_name = simpledialog.askstring("Input", "Enter the character name you want to edit:")
        if not asked_char_name:
            messagebox.showerror("Error", "Character name cannot be empty.")
            return
        
        import_data, import_path = load_file_from_char_name(asked_char_name, char_name)

        return import_data, import_path

    else:
        messagebox.showerror("Error", "Please select a valid userdata (ps4) or DS30000.sl2 file. If your are on seamless, rename your file to DS30000.sl2 ")
        return
    
def import_save(data):
    global MODE

    current_steam_id, current_steam_offset=check_steam_id(data)
    if current_steam_id is None:
        print('can not import save. steam id not found')
        return
    
    import_data, import_path=open_file_import()

    if import_data is None and import_path is None:
        return
    
    old_steam_id, old_steam_offset =check_steam_id(import_data)
    if old_steam_id is None:
        print('can not import save. steam id not found')
        return
    
    data=bytearray(import_data)

    data= bytearray(data[:old_steam_offset] + current_steam_id + data[old_steam_offset+8:])

    return data # after done improting , we re parse and update every thing
    




def main():

    data, path= open_file()
    
    if data is None:
        print('No file selected or failed to read file.')
        return
    


    save_file(data, path)

    return




    
if __name__ == "__main__":
    main()

