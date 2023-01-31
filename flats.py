import unittest

class Flat(object):
    id = None
    floor = None
    entrance = None
    residents = []
    up_ids = []
    down_ids = []

    def __init__(self, number, entrance, floor, up_ids=None, down_ids=None):
        if up_ids is None:
            up_ids = []
        self.id = number
        self.floor = floor
        self.entrance = entrance
        self.residents = []
        if up_ids:
            self.up_ids = up_ids
        else:
            self.up_ids = []
        if down_ids:
            self.down_ids = down_ids
        else:
            self.down_ids = []

    def __str__(self):
        return '(Flat №{0}, floor {1}, en {2}: {3} | ({4},{5}))'.format(self.id, self.floor,
                                                                        self.entrance, self.residents,
                                                                        self.up_ids, self.down_ids)

    def addResident(self, resident_tg_id):
        if resident_tg_id not in self.residents:
            self.residents.append(resident_tg_id)

    def removeResident(self, resident_tg_id):
        self.residents.remove(resident_tg_id)

    def get_floor_neighbors(self, flats_in_entrance_list, with_same_flat_residents=False):
        neighbors = []
        for f in flats_in_entrance_list:
            if ((f.id != self.id) or with_same_flat_residents) and (f.floor == self.floor):
                neighbors += f.residents
        return neighbors

    def get_up_neighbors(self, flats_in_entrance_list):
        neighbors = []
        for id in self.up_ids:
            neighbors += find_by_flat_id(flats_in_entrance_list, id).residents
        return neighbors

    def get_down_neighbors(self, flats_in_entrance_list):
        neighbors = []
        for id in self.down_ids:
            neighbors += find_by_flat_id(flats_in_entrance_list, id).residents
        return neighbors


def find_by_flat_id(flats_list, id):
    for f in flats_list:
        if id == f.id:
            return f
    return None


def find_by_person(flats_list, person_tg_id):
    for f in flats_list:
        if person_tg_id in f.residents:
            return f
    return None


def flats_at_entrance_struct(entrance_id, first_flat, last_flat, first_floor, flats_count, start_counter=0):
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


def halkon_flats_struct():
    halkon_flats = {1: [], 'v': [], 2: [], 3: [], 4: [], 'k': []}
    '''#1 '''
    halkon_flats[1] = flats_at_entrance_struct(1, 1, 18, first_floor=3, flats_count=3)
    find_by_flat_id(halkon_flats[1], 14).up_ids.append(16)
    find_by_flat_id(halkon_flats[1], 16).down_ids.append(14)
    '''#villas '''
    halkon_flats['v'] = flats_at_entrance_struct('v', 19, 22, first_floor=1, flats_count=4)

    '''#2 '''
    halkon_flats[2] = flats_at_entrance_struct(2, 23, 41, first_floor=2, flats_count=3, start_counter=2)
    find_by_flat_id(halkon_flats[2], 41).up_ids.append(56)

    '''#3 '''
    halkon_flats[3] = flats_at_entrance_struct(3, 42, 57, first_floor=2, flats_count=2)
    find_by_flat_id(halkon_flats[3], 56).down_ids.append(41)

    '''#4 '''
    halkon_flats[4] = flats_at_entrance_struct(4, 58, 72, first_floor=2, flats_count=2, start_counter=1)

    return halkon_flats


class FlatsTest(unittest.TestCase):

    def test_addresident(self):
        f = Flat(1, 1, 7)
        print(f)
        id = '1'
        f.addResident(id)
        f.addResident(id)
        self.assertEqual(f.residents, [id])
        print(f)
        f.removeResident(id)
        self.assertEqual(f.residents, [])
        print(f)
        print('---')
        for e in halkon_flats_struct().values():
            for y in e:
                print(y)
