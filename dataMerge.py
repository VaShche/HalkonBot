import flats
import func
import settings

conf = settings.config

key = conf['BOT']['cryptokey']
'''
house_data = func.load_dict_from_file(conf['BOT']['data'])
func.save_dict_to_file('old_'+conf['BOT']['data'], house_data)

func.save_dict_to_file(conf['BOT']['data'], house_data, key=conf['BOT']['cryptokey'])
house_data_merged = func.load_dict_from_file(conf['BOT']['data'], key=key)
'''
house_data = func.load_dict_from_file(conf['BOT']['data'], key=key)
l1 = [42, 44, 46, 48, 50, 52, 54, 43, 45, 47, 49, 51, 53, 55, 57]
l2 = [23, 26, 29, 32, 35, 38, 41, 58, 59, 61, 63, 65, 67, 69, 71]
for i, n in enumerate(l1):
    flats.Flat.findByFlatID(flats.getAllHouseFlats(house_data), n).wall_residents.append(l2[i])
    flats.Flat.findByFlatID(flats.getAllHouseFlats(house_data), l2[i]).wall_residents.append(n)
func.save_dict_to_file(conf['BOT']['data'], house_data, key=conf['BOT']['cryptokey'])

print(house_data)