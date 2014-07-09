#!/usr/bin/env python3

import sys
import urllib.request
import urllib.parse

import xml.etree.ElementTree as etree


class EveApi:
    base_url = 'https://api.eveonline.com'
    central_url = 'http://api.eve-central.com'
    jita_id = '30000142'

    def __init__(self, name, key_id, v_code):
        self.name = name
        self.key_id = key_id
        self.v_code = v_code

        # set up proxy handler
        proxies = {
            'http': 'http://127.0.0.1:3128/',
            'https': 'http://127.0.0.1:3128/'
        }
        proxy_handler = urllib.request.ProxyHandler(proxies)
        opener = urllib.request.build_opener(proxy_handler)
        # install it globally so it can be used with urlopen.
        urllib.request.install_opener(opener)

        self.serverStatus = None
        self.character_id = self.get_character_id()

    @classmethod
    def u(cls, url):
        return ''.join((cls.base_url, url))

    @classmethod
    def c(cls, url):
        return ''.join((cls.central_url, url))

    def get_server_status(self):
        response = urllib.request.urlopen(self.u('/server/ServerStatus.xml.aspx'))
        if response.status != 200:
            print('Unable to get server status')  # ToDo: raise an exception
            return ''
        xml_raw = response.read()
        self.serverStatus = etree.fromstring(xml_raw)

    @property
    def online_players(self):
        if self.serverStatus is None:
            self.get_server_status()
        p = self.serverStatus.find('result/onlinePlayers')
        return '' if p is None else p.text

    @property
    def current_time(self):
        if self.serverStatus is None:
            self.get_server_status()
        t = self.serverStatus.find('currentTime')
        return '' if t is None else t.text

    def get_character_id(self):
        result = ''
        data = urllib.parse.urlencode({'names': self.name})
        response = urllib.request.urlopen(self.u('/eve/CharacterID.xml.aspx'), data.encode())
        if response.status != 200:
            print('Unable to get character id')  # ToDo: raise an exception
            return ''
        xml_raw = response.read()
        root = etree.fromstring(xml_raw)
        for n in root.iter('row'):
            if self.name == n.attrib['name']:
                result = n.attrib['characterID']
        return result

    @property
    def account_balance(self):
        params = {
            'keyID': self.key_id,
            'vCode': self.v_code,
            'characterID': self.character_id,
        }
        data = urllib.parse.urlencode(params)
        response = urllib.request.urlopen(self.u('/char/AccountBalance.xml.aspx'), data.encode())
        if response.status != 200:
            print('Unable to get account balance')  # ToDo: raise an exception
            return ''
        xml_raw = response.read()
        root = etree.fromstring(xml_raw)
        balance = root.find('result/rowset/row')  # ToDo: empty or invalid response handler
        return balance.attrib['balance']

    @property
    def wallet_transactions(self):
        result = []
        params = {
            'keyID': self.key_id,
            'vCode': self.v_code,
            'characterID': self.character_id,
        }
        data = urllib.parse.urlencode(params)
        response = urllib.request.urlopen(self.u('/char/WalletTransactions.xml.aspx'), data.encode())
        if response.status != 200:
            print('Unable to get character id')  # ToDo: raise an exception
            return ''
        xml_raw = response.read()
        root = etree.fromstring(xml_raw)
        for n in root.iter('row'):
            result.append(n.attrib)
        return result

    def marketstat(self, items):
        params = [
            ('usesystem', self.jita_id),
        ]
        result = {}
        for i in items:
            params.append(('typeid', i))

        data = urllib.parse.urlencode(params)
        response = urllib.request.urlopen(self.c('/api/marketstat'), data.encode())
        if response.status != 200:
            print('Unable to central market data')  # ToDo: raise an exception
            return ''
        xml_raw = response.read()
        root = etree.fromstring(xml_raw)
        for n in root.iter('type'):
            avg = n.find('sell/min')
            result[n.attrib['id']] = avg.text
        return result


def main():
    name = 'Murometc'
    key_id = '3512512'
    v_code = 'D4SZNnU7g2XPiLb7EgCPKKBRUySWM2zl6QOXduqWWRPeDvdmU4okASp4ExCpcT4Y'

    balance = 0.0

    api = EveApi(name, key_id, v_code)
    print('Total balance: {}'.format(api.account_balance))

    items = []
    transactions = api.wallet_transactions

    for transaction in transactions:
        items.append(transaction['typeID'])

    marketstat = api.marketstat(items)

    for n in transactions:
        sell_price = float(n['price'])
        jita_price = float(marketstat[n['typeID']])
        quanity = float(n['quantity'])

        print('{transactionDateTime},{quantity},{typeName},{price}'.format_map(n), end=',')
        print(jita_price, end=',')
        profit = sell_price*quanity - jita_price*quanity
        print('{}'.format(profit))
        balance += profit

    print('Balance change: {}'.format(balance))

if __name__ == '__main__':
    sys.exit(main())
