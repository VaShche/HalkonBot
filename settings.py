import os
import configparser

config = {'BOT': dict(), 'MC': dict()}

if os.path.exists('settings.ini'):
    conf = configparser.ConfigParser()
    conf.read('settings.ini')
    os.environ["HALKONBOT_BOT_TOKEN"] = str(conf['BOT']['token'])
    os.environ["HALKONBOT_BOT_CHAT"] = str(conf['BOT']['chatid'])
    os.environ["HALKONBOT_BOT_CHANNEL"] = str(conf['BOT']['channelid'])
    os.environ["HALKONBOT_BOT_SERVICECHAT"] = str(conf['BOT']['servicechatid'])
    os.environ["HALKONBOT_BOT_DATA"] = str(conf['BOT']['data'])
    os.environ["HALKONBOT_BOT_LINK"] = str(conf['BOT']['invitelink'])
    os.environ["HALKONBOT_BOT_ADMIN"] = str(conf['BOT']['adminid'])
    os.environ["HALKONBOT_BOT_CRYPTOKEY"] = str(conf['BOT']['cryptokey'])
    os.environ["HALKONBOT_BOT_NAME"] = str(conf['BOT']['name'])
    os.environ["HALKONBOT_BOT_CHANNEL_NAME"] = str(conf['BOT']['channelname'])

    os.environ["HALKONBOT_MC_PHONE"] = str(conf['MC']['phone'])
    os.environ["HALKONBOT_MC_NAME"] = str(conf['MC']['name'])
    os.environ["HALKONBOT_MC_LN"] = str(conf['MC']['lastname'])

config['BOT']['token'] = os.getenv("HALKONBOT_BOT_TOKEN")
config['BOT']['chatid'] = os.getenv("HALKONBOT_BOT_CHAT")
config['BOT']['channelid'] = os.getenv("HALKONBOT_BOT_CHANNEL")
config['BOT']['servicechatid'] = os.getenv("HALKONBOT_BOT_SERVICECHAT")
config['BOT']['data'] = os.getenv("HALKONBOT_BOT_DATA")
config['BOT']['invitelink'] = os.getenv("HALKONBOT_BOT_LINK")
config['BOT']['adminid'] = os.getenv("HALKONBOT_BOT_ADMIN")
config['BOT']['cryptokey'] = os.getenv("HALKONBOT_BOT_CRYPTOKEY")
config['BOT']['name'] = os.getenv("HALKONBOT_BOT_NAME")
config['BOT']['channelname'] = os.getenv("HALKONBOT_BOT_CHANNEL_NAME")

config['MC']['phone'] = os.getenv("HALKONBOT_MC_PHONE")
config['MC']['name'] = os.getenv("HALKONBOT_MC_NAME")
config['MC']['lastname'] = os.getenv("HALKONBOT_MC_LN")