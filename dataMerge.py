import flats
import func
import configparser

conf = configparser.ConfigParser()
conf.read('settings.ini')

key = conf['BOT']['cryptokey']

house_data = func.load_dict_from_file(conf['BOT']['data'])
func.save_dict_to_file('old_'+conf['BOT']['data'], house_data)

func.save_dict_to_file(conf['BOT']['data'], house_data, key=conf['BOT']['cryptokey'])
house_data_merged = func.load_dict_from_file(conf['BOT']['data'], key=key)

print(house_data == house_data_merged)
print(house_data)
print(house_data_merged)