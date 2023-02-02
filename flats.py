import unittest

class Resident(object):
    id = None
    chat_id = None
    status_id = None
    statuses = {0: "Не подтверждён", 1: "Живёт в ЖК", 2: "Собственник в ЖК"}
    flat_id = None
    status_granted_by = None

    def __init__(self, id, chat_id, flat_id=None):
        self.id = id
        self.chat_id = chat_id
        self.flat_id = flat_id
        self.status_id = 0

    def setStatus(self, status_id, by):
        self.status_id = status_id
        self.status_granted_by = by

    def __str__(self):
        return '{0} - {1} in {2} ({3})'.format(self.id, self.statuses.get(self.status_id),
                                               self.flat_id, self.status_granted_by)

    @staticmethod
    def getResidentsIDs(residents_list):
        residents_ids = []
        for r in residents_list:
            residents_ids.append(r.id)
        return residents_ids

    @staticmethod
    def findByTgID(residents_list, tg_id):
        for r in residents_list:
            if r.id == tg_id:
                return r
        return None


class Flat(object):
    id = None
    floor = None
    entrance = None
    residents = []
    up_residents = []
    down_residents = []

    def __init__(self, number, entrance, floor, up_residents=None, down_residents=None):
        self.id = number
        self.floor = floor
        self.entrance = entrance
        self.residents = []
        if up_residents:
            self.up_residents = up_residents
        else:
            self.up_residents = []
        if down_residents:
            self.down_residents = down_residents
        else:
            self.down_residents = []

    def __str__(self):
        return '(Flat №{0}, floor {1}, en {2}: {3} | ({4},{5}))'.format(self.id, self.floor,
                                                                        self.entrance, self.residents,
                                                                        self.up_residents, self.down_residents)

    def addResident(self, resident_tg_id, chat_id):
        if resident_tg_id not in Resident.getResidentsIDs(self.residents):
            self.residents.append(Resident(resident_tg_id, chat_id, self.id))

    def removeResident(self, resident_tg_id):
        r = Resident.findByTgID(self.residents, resident_tg_id)
        if r:
            self.residents.remove(r)

    def getFloorNeighbors(self, flats_in_entrance_list, with_same_flat_residents=False):
        neighbors = []
        for f in flats_in_entrance_list:
            if ((f.id != self.id) or with_same_flat_residents) and (f.floor == self.floor):
                neighbors += f.residents
        return neighbors

    def getUpNeighbors(self, flats_in_entrance_list):
        neighbors = []
        for id in self.up_residents:
            neighbors += self.findByFlatID(flats_in_entrance_list, id).residents
        return neighbors

    def getDownNeighbors(self, flats_in_entrance_list):
        neighbors = []
        for id in self.down_residents:
            neighbors += self.findByFlatID(flats_in_entrance_list, id).residents
        return neighbors

    def getAllNeighbors(self, flats_in_entrance_list):
        neighbors = []
        for f in flats_in_entrance_list:
            neighbors += f.residents
        return neighbors


    @staticmethod
    def findByFlatID(flats_list, flat_id):
        for f in flats_list:
            if flat_id == f.id:
                return f
        return None

    @staticmethod
    def findByPerson(flats_list, person_tg_id):
        for f in flats_list:
            if person_tg_id in Resident.getResidentsIDs(f.residents):
                return f
        return None


def getFlatsAtEntranceStruct(entrance_id, first_flat, last_flat, first_floor, flats_count, start_counter=0):
    """
    :param entrance_id: entrance for flats id
    :param first_flat: № of first flat in entrance
    :param last_flat: № of last flat in entrance
    :param first_floor: № of first floor with flats
    :param flats_count: count of flats at floor
    :param start_counter: in case of less flats on first floor
    :return: list of Flats objects for entrance
    """
    flats = []
    i = start_counter
    floor = first_floor
    flats_list = list(range(first_flat, last_flat + 1))
    for id in flats_list:
        if i == flats_count:
            i = 0
            floor += 1
            flats.append(Flat(None, entrance_id, floor))  # for case when we have only floor and entrance
        i += 1
        up_id = []
        if id + flats_count in flats_list:
            up_id = [id + flats_count]
        down_id = []
        if id - flats_count in flats_list:
            down_id = [id - flats_count]
        flats.append(Flat(id, entrance_id, floor, up_id, down_id))
    return flats


def getHalkonFlatsStruct():
    halkon_flats = {1: [], 'v': [], 2: [], 3: [], 4: [], 'k': []}
    '''#1 '''
    halkon_flats[1] = getFlatsAtEntranceStruct(1, 1, 18, first_floor=3, flats_count=3)
    Flat.findByFlatID(halkon_flats[1], 14).up_residents.append(16)
    Flat.findByFlatID(halkon_flats[1], 16).down_residents.append(14)
    '''#villas '''
    halkon_flats['v'] = getFlatsAtEntranceStruct('v', 19, 22, first_floor=1, flats_count=4)

    '''#2 '''
    halkon_flats[2] = getFlatsAtEntranceStruct(2, 23, 41, first_floor=2, flats_count=3, start_counter=2)
    Flat.findByFlatID(halkon_flats[2], 41).up_residents.append(56)

    '''#3 '''
    halkon_flats[3] = getFlatsAtEntranceStruct(3, 42, 57, first_floor=2, flats_count=2)
    Flat.findByFlatID(halkon_flats[3], 56).down_residents.append(41)

    '''#4 '''
    halkon_flats[4] = getFlatsAtEntranceStruct(4, 58, 72, first_floor=2, flats_count=2, start_counter=1)

    return halkon_flats

def getAllHouseFlats(house_dict):
    flats_list = []
    for flats in house_dict.values():
        flats_list += flats
    return flats_list


def getAllHouseResidents(house_dict):
    res_list = []
    flats = getAllHouseFlats(house_dict)
    for f in flats:
        res_list += f.residents
    return res_list


class FlatsTest(unittest.TestCase):

    def test_addresident(self):
        f = Flat(1, 1, 7)
        print(f)
        tg_id = 1
        f.addResident(tg_id, tg_id)
        res = f.residents
        f.addResident(tg_id, tg_id)
        self.assertEqual(f.residents, res)
        print(f)
        f.removeResident(tg_id)
        self.assertEqual(f.residents, [])
        print(f)
        print('---')

        print(getAllHouseFlats(getHalkonFlatsStruct()))
        print(getAllHouseResidents(getHalkonFlatsStruct()))
