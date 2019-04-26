#!/usr/bin/env python3
#
# Part of `StashNodeMonitorBot`
#
# Copyright 2018 dustinface
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
##

import configparser
import logging
import sys, argparse, os
import json

from src import database
from src import telegram
from src import discord

from src.stashnodes import StashNodeList

from stashpay.rpc import RPCConfig
#from stashpay.rewardlist import SNRewardList

__version__ = "2.0"

def checkConfig(config,category, name):
    try:
        config.get(category,name)
    except configparser.NoSectionError as e:
        sys.exit("Config error {}".format(e))
    except configparser.NoOptionError as e:
        sys.exit("Config value error {}".format(e))

def main(argv):

    directory = os.path.dirname(os.path.realpath(__file__))
    config = configparser.SafeConfigParser()

    try:
        config.read(directory + '/stash.conf')
    except:
        sys.exit("Config file missing or corrupt.")

    checkConfig(config, 'bot','token')
    checkConfig(config, 'bot','app')
    checkConfig(config, 'general','loglevel')
    checkConfig(config, 'general','githubuser')
    checkConfig(config, 'general','githubpassword')
    checkConfig(config, 'general','environment')
    checkConfig(config, 'rpc','url')
    checkConfig(config, 'rpc','port')
    checkConfig(config, 'rpc','username')
    checkConfig(config, 'rpc','password')
    checkConfig(config, 'rpc','timeout')

    if config.get('bot', 'app') != 'telegram' and\
       config.get('bot', 'app') != 'discord':
        sys.exit("You need to set 'telegram' or 'discord' as 'app' in the configfile.")

    # Set the log level
    level = int(config.get('general','loglevel'))

    if level < 0 or level > 4:
        sys.exit("Invalid log level.\n 1 - debug\n 2 - info\n 3 - warning\n 4 - error")

    # Enable logging

    environment = int(config.get('general','environment'))

    if environment != 1 and\
       environment != 2:
       sys.exit("Invalid environment.\n 1 - development\n 2 - production\n")

    if environment == 1: # development
        logging.basicConfig(format='%(asctime)s - monitor_{} - %(name)s - %(levelname)s - %(message)s'.format(config.get('bot', 'app')),
                        level=level*10)
    else:# production
        logging.basicConfig(format='monitor_{} %(name)s - %(levelname)s - %(message)s'.format(config.get('bot', 'app')),
                        level=level*10)


    rpcUrl = config.get('rpc','url')
    rpcPort = config.get('rpc','port')
    rpcUser = config.get('rpc','username')
    rpcPassword = config.get('rpc','password')
    rpcTimeout = int(config.get('rpc','timeout'))

    rpcConfig = RPCConfig(rpcUser, rpcPassword, rpcUrl, rpcPort, rpcTimeout)

    # Load the user database
    botdb = database.BotDatabase(directory + '/bot.db')

    # Load the stashnodes database
    nodedb = database.NodeDatabase(directory + '/nodes.db')

    admins = []
    password = None

    try:
        admins = config.get('optional','admins').split(',')
    except:
        pass

    try:
        password = config.get('optional','password')
    except:
        pass

    githubUser = config.get('general','githubuser')
    githubPassword = config.get('general','githubpassword')

    # Create the stashnode list
    nodeList = StashNodeList(nodedb, rpcConfig)

    # Create the stashnode reward list
    #rewardList = SNRewardList(directory + '/rewards.db', rpcConfig)

    nodeBot = None

    if config.get('bot', 'app') == 'telegram':
        nodeBot = telegram.StashNodeBotTelegram(config.get('bot','token'), admins, password, botdb, nodeList)
    elif config.get('bot', 'app') == 'discord':
        nodeBot = discord.StashNodeBotDiscord(config.get('bot','token'), admins, password, botdb, nodeList)
    else:
        sys.exit("You need to set 'telegram' or 'discord' as 'app' in the configfile.")

    # Start and run forever!
    nodeBot.start()

if __name__ == '__main__':
    main(sys.argv[1:])
