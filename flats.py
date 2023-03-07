import unittest
import math
from constants import *


class Resident(object):
    id = None
    chat_id = None
    status_id = None
    statuses = {0: "не подтверждён", 1: "живёт в ЖК", 2: "собственник в ЖК"}
    flat_id = None
    status_granted_by = None
    adding_user_id = None
    adding_user_flat_id = None

    def __init__(self, tg_id, chat_id, flat_id=None):
        self.id = tg_id
        self.chat_id = chat_id
        self.flat_id = flat_id
        self.status_id = 0
        self.adding_user_id = None
        self.adding_user_flat_id = None

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
    wall_residents = []

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
        self.wall_residents = []

    def __str__(self):
        return '(Flat №{0}, floor {1}, en {2}: {3} | ({4},{5}))'.format(self.id, self.floor,
                                                                        self.entrance, self.residents,
                                                                        self.up_residents, self.down_residents)

    def find_resident(self, resident_tg_id):
        for r in self.residents:
            if r.id == resident_tg_id:
                return r
        return None

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
            if ((f.id != self.id) or with_same_flat_residents) and f.floor == self.floor:
                neighbors += f.residents
        return neighbors

    def getUpNeighbors(self, all_home_flats):
        neighbors = []
        for tg_id in self.up_residents:
            neighbors += self.findByFlatID(all_home_flats, tg_id).residents
        return neighbors

    def getDownNeighbors(self, all_home_flats):
        neighbors = []
        for tg_id in self.down_residents:
            neighbors += self.findByFlatID(all_home_flats, tg_id).residents
        return neighbors

    def get_wall_neighbors(self, all_home_flats):
        neighbors = []
        for tg_id in self.wall_residents:
            neighbors += self.findByFlatID(all_home_flats, tg_id).residents
        return neighbors

    def getAllNeighbors(self, flats_in_entrance_list, with_same_flat_residents=True):
        neighbors = []
        for f in flats_in_entrance_list:
            if (f.id != self.id) or with_same_flat_residents:
                neighbors += f.residents
        return neighbors

    def closest_neighbors(self, flats_dict):
        if len(self.residents) > 1:
            return self.residents
        flats_list = flats_dict.get(self.entrance)
        all_flats_list = getAllHouseFlats(flats_dict)
        neighbors_list = self.getFloorNeighbors(flats_list, with_same_flat_residents=False)
        neighbors_list += self.get_wall_neighbors(all_flats_list)
        neighbors_list += self.getUpNeighbors(all_flats_list)
        neighbors_list += self.getDownNeighbors(all_flats_list)
        if not neighbors_list:
            neighbors_list = self.getAllNeighbors(flats_list)
        if not neighbors_list:
            neighbors_list = getAllHouseResidents(flats_dict)
        return neighbors_list

    def get_floors_for_check(self, max_floor=9, min_floor=1):
        step = math.floor(max_floor/4)
        floors = [self.floor]
        while len(floors) < 4:
            next_floor = floors[-1] - step
            if next_floor < min_floor:
                next_floor = max_floor - (min_floor - next_floor)
            floors.append(next_floor)
        floors.sort()
        return floors

    @staticmethod
    def findByFlatID(flats_list, flat_id):
        for f in flats_list:
            if flat_id == f.id:
                return f
        return None

    @staticmethod
    def findByPerson(flats_list, person_tg_id):
        for f in flats_list:
            if f.find_resident(person_tg_id):
                return f
        return None


def getFlatsAtEntranceStruct(entrance_id, first_flat, last_flat, first_floor, flats_count, start_counter=0):
    """
    :param entrance_id: entrance for flats id
    :param first_flat: № of first flat in entrance
    :param last_flat: № of last flat in entrance
    :param first_floor: № of first floor with flats
    :param flats_count: count of flats at floor
    :param start_counter: in case of fewer flats on first floor
    :return: list of Flats objects for entrance
    """
    flats = []
    i = start_counter
    floor = first_floor
    flats_list = list(range(first_flat, last_flat + 1))
    for flat_id in flats_list:
        if i == flats_count:
            i = 0
            floor += 1
            flats.append(Flat(None, entrance_id, floor))  # for case when we have only floor and entrance
        i += 1
        up_id = []
        if flat_id + flats_count in flats_list:
            up_id = [flat_id + flats_count]
        down_id = []
        if flat_id - flats_count in flats_list:
            down_id = [flat_id - flats_count]
        flats.append(Flat(flat_id, entrance_id, floor, up_id, down_id))
    return flats


def getHalkonFlatsStruct():
    halkon_flats = dict()
    '''#1 '''
    entrance = 'Парадная №1'
    halkon_flats[entrance] = getFlatsAtEntranceStruct(entrance, 1, 18, first_floor=3, flats_count=3)
    Flat.findByFlatID(halkon_flats[entrance], 14).up_residents.append(16)
    Flat.findByFlatID(halkon_flats[entrance], 16).down_residents.append(14)
    '''#villas '''
    entrance = 'Сити-виллы'
    halkon_flats[entrance] = getFlatsAtEntranceStruct(entrance, 19, 22, first_floor=1, flats_count=4)
    '''#2 '''
    entrance = 'Парадная №2'
    halkon_flats[entrance] = getFlatsAtEntranceStruct(entrance, 23, 41, first_floor=2, flats_count=3, start_counter=2)
    Flat.findByFlatID(halkon_flats[entrance], 41).up_residents.append(56)
    '''#3 '''
    entrance = 'Парадная №3'
    halkon_flats[entrance] = getFlatsAtEntranceStruct(entrance, 42, 57, first_floor=2, flats_count=2)
    Flat.findByFlatID(halkon_flats[entrance], 56).down_residents.append(41)
    '''#4 '''
    entrance = 'Парадная №4'
    halkon_flats[entrance] = getFlatsAtEntranceStruct(entrance, 58, 72, first_floor=2, flats_count=2, start_counter=1)
    l1 = [42, 44, 46, 48, 50, 52, 54, 43, 45, 47, 49, 51, 53, 55, 57]
    l2 = [23, 26, 29, 32, 35, 38, 41, 58, 59, 61, 63, 65, 67, 69, 71]
    for i, n in enumerate(l1):
        Flat.findByFlatID(getAllHouseFlats(halkon_flats), n).wall_residents = [l2[i]]
        Flat.findByFlatID(getAllHouseFlats(halkon_flats), l2[i]).wall_residents = [n]
    '''коммерция'''
    entrance = COMMERCE
    halkon_flats[entrance] = [Flat(None, entrance, 1)]
    '''окружающие'''
    entrance = OTHER
    halkon_flats[entrance] = [Flat(BAN, entrance, 1), Flat(INTERESTED, entrance, 1), Flat(CLOSELIVING, entrance, 1)]
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


def get_text_statistics(house_dict):
    start_text = 'На данный момент зарегестрировались в боте:'
    message_text = ''
    total_flats_counter = 0
    for entrance in house_dict.keys():
        res_list = []
        flats_counter = 0
        for f in house_dict.get(entrance):
            if f.id and f.residents:
                flats_counter += 1
            res_list += f.residents
        if res_list and entrance == COMMERCE:
            message_text += '\n<i>{}</i> - {} представителей из <b>{}</b> компаний'.format(entrance, len(res_list),
                                                                                           flats_counter)
        elif res_list and entrance == OTHER:
            message_text += '\n<i>{}</i> - {} интересующихся или живущих рядом'.format(entrance, len(res_list))
        elif res_list:
            total_flats_counter += flats_counter
            message_text += '\n<b>{}</b> - <b>{}</b> человек из <b>{}</b> квартир'.format(entrance, len(res_list),
                                                                                          flats_counter)
    flats_percent = round(total_flats_counter / 0.72)
    flats_percent_text = '\n\n'
    for x in range(0, round(flats_percent * 0.1)):
        flats_percent_text += '🟩'
    for x in range(round(flats_percent * 0.1), 10):
        flats_percent_text += '🔲'
    flats_percent_text += '<b> {}%</b>\n'.format(flats_percent)
    return start_text + flats_percent_text + message_text


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
        r = f.find_resident(1)
        r.adding_user_id = 2
        self.assertEqual(r.adding_user_id, f.find_resident(1).adding_user_id)
        print(f.find_resident(1).adding_user_id)
        f.removeResident(tg_id)
        self.assertEqual(f.residents, [])
        print(f)
        print('---')

        print(getAllHouseFlats(getHalkonFlatsStruct()))
        print(getAllHouseResidents(getHalkonFlatsStruct()))

    def test_get_floors_for_check(self):
        f = Flat(1, 1, 1)
        self.assertEqual(f.get_floors_for_check(), [1, 3, 5, 7])
        f = Flat(1, 1, 9)
        self.assertEqual(f.get_floors_for_check(), [3, 5, 7, 9])
        f = Flat(1, 1, 8)
        self.assertEqual(f.get_floors_for_check(), [2, 4, 6, 8])
        f = Flat(1, 1, 6)
        self.assertEqual(f.get_floors_for_check(), [2, 4, 6, 8])
        f = Flat(1, 1, 7)
        self.assertEqual(f.get_floors_for_check(), [1, 3, 5, 7])
