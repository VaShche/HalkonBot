import os
import configparser

config = {'BOT': dict(), 'MC': dict()}

if os.path.exists('settings.ini'):
    conf = configparser.ConfigParser()
    conf.read('settings.ini')
    os.environ["ZKBOT_BOT_TOKEN"] = str(conf['BOT']['token'])
    os.environ["ZKBOT_BOT_CHAT"] = str(conf['BOT']['chatid'])
    os.environ["ZKBOT_BOT_CHANNEL"] = str(conf['BOT']['channelid'])
    os.environ["ZKBOT_BOT_SERVICECHAT"] = str(conf['BOT']['servicechatid'])
    os.environ["ZKBOT_BOT_DATA"] = str(conf['BOT']['data'])
    os.environ["ZKBOT_BOT_LINK"] = str(conf['BOT']['invitelink'])
    os.environ["ZKBOT_BOT_ADMIN"] = str(conf['BOT']['adminid'])
    os.environ["ZKBOT_BOT_CRYPTOKEY"] = str(conf['BOT']['cryptokey'])
    os.environ["ZKBOT_BOT_NAME"] = str(conf['BOT']['name'])
    os.environ["ZKBOT_BOT_CHANNEL_NAME"] = str(conf['BOT']['channelname'])

    os.environ["ZKBOT_MC_PHONE"] = str(conf['MC']['phone'])
    os.environ["ZKBOT_MC_NAME"] = str(conf['MC']['name'])
    os.environ["ZKBOT_MC_LN"] = str(conf['MC']['lastname'])

config['BOT']['token'] = os.getenv("ZKBOT_BOT_TOKEN")
config['BOT']['chatid'] = os.getenv("ZKBOT_BOT_CHAT")
config['BOT']['channelid'] = os.getenv("ZKBOT_BOT_CHANNEL")
config['BOT']['servicechatid'] = os.getenv("ZKBOT_BOT_SERVICECHAT")
config['BOT']['data'] = os.getenv("ZKBOT_BOT_DATA")
config['BOT']['invitelink'] = os.getenv("ZKBOT_BOT_LINK")
config['BOT']['adminid'] = os.getenv("ZKBOT_BOT_ADMIN")
config['BOT']['cryptokey'] = os.getenv("ZKBOT_BOT_CRYPTOKEY")
config['BOT']['name'] = os.getenv("ZKBOT_BOT_NAME")
config['BOT']['channelname'] = os.getenv("ZKBOT_BOT_CHANNEL_NAME")

config['MC']['phone'] = os.getenv("ZKBOT_MC_PHONE")
config['MC']['name'] = os.getenv("ZKBOT_MC_NAME")
config['MC']['lastname'] = os.getenv("ZKBOT_MC_LN")