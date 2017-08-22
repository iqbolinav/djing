# -*- coding: utf-8 -*-
import socket
import binascii
from abc import ABCMeta
from hashlib import md5
from .core import BaseTransmitter, NasFailedResult, NasNetworkError
from mydefs import ping
from .structs import TariffStruct, AbonStruct, IpStruct
from . import settings
from djing.settings import DEBUG
import re


#DEBUG=True

LIST_USERS_ALLOWED = 'DjingUsersAllowed'
LIST_USERS_BLOCKED = 'DjingUsersBlocked'


class ApiRos:
    "Routeros api"

    def __init__(self, sk):
        self.sk = sk
        self.currenttag = 0

    def login(self, username, pwd):
        chal = None
        for repl, attrs in self.talk_iter(["/login"]):
            chal = binascii.unhexlify(attrs['=ret'])
        md = md5()
        md.update(b'\x00')
        md.update(bytes(pwd, 'utf-8'))
        md.update(chal)
        for r in self.talk_iter(["/login", "=name=" + username,
                                 "=response=00" + binascii.hexlify(md.digest()).decode('utf-8')]): pass

    def talk_iter(self, words):
        if self.writeSentence(words) == 0: return
        while 1:
            i = self.readSentence()
            if len(i) == 0: continue
            reply = i[0]
            attrs = {}
            for w in i[1:]:
                j = w.find('=', 1)
                if (j == -1):
                    attrs[w] = ''
                else:
                    attrs[w[:j]] = w[j + 1:]
            yield (reply, attrs)
            if reply == '!done': return

    def writeSentence(self, words):
        ret = 0
        for w in words:
            self.writeWord(w)
            ret += 1
        self.writeWord('')
        return ret

    def readSentence(self):
        r = []
        while 1:
            w = self.readWord()
            if w == '': return r
            r.append(w)

    def writeWord(self, w):
        if DEBUG:
            print("<<< " + w)
        b = bytes(w, "utf-8")
        self.writeLen(len(b))
        self.writeBytes(b)

    def readWord(self):
        ret = self.readBytes(self.readLen()).decode('utf-8')
        if DEBUG:
            print(">>> " + ret)
        return ret

    def writeLen(self, l):
        if l < 0x80:
            self.writeBytes(bytes([l]))
        elif l < 0x4000:
            l |= 0x8000
            self.writeBytes(bytes([(l >> 8) & 0xff, l & 0xff]))
        elif l < 0x200000:
            l |= 0xC00000
            self.writeBytes(bytes([(l >> 16) & 0xff, (l >> 8) & 0xff, l & 0xff]))
        elif l < 0x10000000:
            l |= 0xE0000000
            self.writeBytes(bytes([(l >> 24) & 0xff, (l >> 16) & 0xff, (l >> 8) & 0xff, l & 0xff]))
        else:
            self.writeBytes(bytes([0xf0, (l >> 24) & 0xff, (l >> 16) & 0xff, (l >> 8) & 0xff, l & 0xff]))

    def readLen(self):
        c = self.readBytes(1)[0]
        if (c & 0x80) == 0x00:
            pass
        elif (c & 0xC0) == 0x80:
            c &= ~0xC0
            c <<= 8
            c += self.readBytes(1)[0]
        elif (c & 0xE0) == 0xC0:
            c &= ~0xE0
            c <<= 8
            c += self.readBytes(1)[0]
            c <<= 8
            c += self.readBytes(1)[0]
        elif (c & 0xF0) == 0xE0:
            c &= ~0xF0
            c <<= 8
            c += self.readBytes(1)[0]
            c <<= 8
            c += self.readBytes(1)[0]
            c <<= 8
            c += self.readBytes(1)[0]
        elif (c & 0xF8) == 0xF0:
            c = self.readBytes(1)[0]
            c <<= 8
            c += self.readBytes(1)[0]
            c <<= 8
            c += self.readBytes(1)[0]
            c <<= 8
            c += self.readBytes(1)[0]
        return c

    def writeBytes(self, s):
        n = 0
        while n < len(s):
            r = self.sk.send(s[n:])
            if r == 0: raise NasFailedResult("connection closed by remote end")
            n += r

    def readBytes(self, length):
        ret = b''
        while len(ret) < length:
            s = self.sk.recv(length - len(ret))
            if len(s) == 0: raise NasFailedResult("connection closed by remote end")
            ret += s
        return ret


class TransmitterManager(BaseTransmitter, metaclass=ABCMeta):
    def __init__(self, login=None, password=None, ip=None, port=None):
        ip = ip or settings.NAS_IP
        if not ping(ip):
            raise NasNetworkError('NAS %s не пингуется' % ip)
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((ip, port or settings.NAS_PORT))
            self.s = s
            self.ar = ApiRos(s)
            self.ar.login(login or settings.NAS_LOGIN, password or settings.NAS_PASSW)
        except ConnectionRefusedError:
            raise NasNetworkError('Подключение к %s отклонено (Connection Refused)' % ip)

    def __del__(self):
        if hasattr(self, 's'):
            self.s.close()

    def _exec_cmd(self, cmd):
        if not isinstance(cmd, list):
            raise TypeError
        result_iter = self.ar.talk_iter(cmd)
        res = []
        for rt in result_iter:
            if rt[0] == '!trap':
                raise NasFailedResult(rt[1]['=message'])
            res.append(rt[1])
        return res

    def _exec_cmd_iter(self, cmd):
        if not isinstance(cmd, list):
            raise TypeError
        result_iter = self.ar.talk_iter(cmd)
        for rt in result_iter:
            if len(rt) < 2:
                continue
            if rt[0] == '!trap':
                raise NasFailedResult(rt[1]['=message'])
            yield rt

    # Строим объект ShapeItem из инфы, присланной из mikrotik'a
    def _build_shape_obj(self, info):
        # Переводим приставку скорости Mikrotik в Mbit/s
        def parse_speed(text_speed):
            text_speed_digit = float(text_speed[:-1] or 0.0)
            text_append = text_speed[-1:]
            if text_append == 'M':
                res = text_speed_digit
            elif text_append == 'k':
                res = text_speed_digit / 1000
            # elif text_append == 'G':
            #    res = text_speed_digit * 0x400
            else:
                res = float(re.sub(r'[a-zA-Z]', '', text_speed)) / 1000 ** 2
            return res

        speeds = info['=max-limit'].split('/')
        t = TariffStruct(
            speedIn=parse_speed(speeds[1]),
            speedOut=parse_speed(speeds[0])
        )
        try:
            a = AbonStruct(
                uid=int(info['=name'][3:]),
                # FIXME: тут в разных микротиках или =target-addresses или =target
                ip=info['=target'][:-3],
                tariff=t,
                is_active=False if info['=disabled'] == 'false' else True
            )
            a.queue_id = info['=.id']
            return a
        except ValueError:
            pass


class QueueManager(TransmitterManager, metaclass=ABCMeta):
    # ищем правило по имени, и возвращаем всю инфу о найденном правиле
    def find(self, name):
        ret = self._exec_cmd(['/queue/simple/print', '?name=%s' % name])
        if len(ret) > 1:
            return self._build_shape_obj(ret[0])

    def add(self, user):
        if not isinstance(user, AbonStruct):
            raise TypeError
        if user.tariff is None or not isinstance(user.tariff, TariffStruct):
            return
        return self._exec_cmd(['/queue/simple/add',
                               '=name=uid%d' % user.uid,
                               # FIXME: тут в разных микротиках или =target-addresses или =target
                               '=target=%s' % str(user.ip),
                               '=max-limit=%.3fM/%.3fM' % (user.tariff.speedOut, user.tariff.speedIn),
                               '=queue=MikroBILL_SFQ/MikroBILL_SFQ',
                               '=burst-time=1/1'
                               ])

    def remove(self, user):
        if not isinstance(user, AbonStruct):
            raise TypeError
        q = self.find('uid%d' % user.uid)
        if q is not None:
            return self._exec_cmd(['/queue/simple/remove', '=.id=' + getattr(q, 'queue_id', '')])

    def remove_range(self, q_ids):
        if q_ids is not None and len(q_ids) > 0:
            return self._exec_cmd(['/queue/simple/remove', '=numbers=' + ','.join(q_ids)])

    def update(self, user):
        if not isinstance(user, AbonStruct):
            raise TypeError
        if user.tariff is None or not isinstance(user.tariff, TariffStruct):
            return
        queue = self.find('uid%d' % user.uid)
        if queue is None:
            # не нашли запись в шейпере об абоненте, добавим
            return self.add(user)
        else:
            mk_id = getattr(queue, 'queue_id', '')
            # обновляем шейпер абонента
            return self._exec_cmd(['/queue/simple/set', '=.id=' + mk_id,
                                   '=name=uid%d' % user.uid,
                                   '=max-limit=%.3fM/%.3fM' % (user.tariff.speedOut, user.tariff.speedIn),
                                   # FIXME: тут в разных микротиках или =target-addresses или =target
                                   '=target=%s' % str(user.ip),
                                   '=queue=MikroBILL_SFQ/MikroBILL_SFQ',
                                   '=burst-time=1/1'
                                   ])

    # читаем шейпер, возващаем записи о шейпере
    def read_queue_iter(self):
        queues = self._exec_cmd_iter(['/queue/simple/print', '=detail'])
        for queue in queues:
            if queue[0] == '!done': return
            sobj = self._build_shape_obj(queue[1])
            if sobj is not None:
                yield sobj

    # то же что и выше, только получаем только номера в микротике
    def read_mikroids_iter(self):
        queues = self._exec_cmd_iter(['/queue/simple/print', '=detail'])
        for queue in queues:
            if queue[0] == '!done': return
            yield int(queue[1]['=.id'].replace('*', ''), base=16)

    def disable(self, user):
        if not isinstance(user, AbonStruct):
            raise TypeError
        q = self.find('uid%d' % user.uid)
        if q is None:
            self.add(user)
            return self.disable(user)
        else:
            return self._exec_cmd(['/queue/simple/disable', '=.id=*' + getattr(q, 'queue_id', '')])

    def enable(self, user):
        if not isinstance(user, AbonStruct):
            raise TypeError
        q = self.find('uid%d' % user.uid)
        if q is None:
            self.add(user)
            self.enable(user)
        else:
            return self._exec_cmd(['/queue/simple/enable', '=.id=*' + getattr(q, 'queue_id', '')])


class IpAddressListObj(IpStruct):
    def __init__(self, ip, mk_id):
        super(IpAddressListObj, self).__init__(ip)
        self.mk_id = str(mk_id).replace('*', '')


class IpAddressListManager(TransmitterManager, metaclass=ABCMeta):

    def add(self, list_name, ip, timeout=None):
        if not isinstance(ip, IpStruct):
            raise TypeError
        commands = [
            '/ip/firewall/address-list/add',
            '=list=%s' % list_name,
            '=address=%s' % str(ip)
        ]
        if type(timeout) is int:
            commands.append('=timeout=%d' % timeout)
        return self._exec_cmd(commands)

    def _edit(self, mk_id, timeout=None):
        if timeout is not None:
            commands = [
                '/ip/firewall/address-list/set', '=.id=' + str(mk_id),
                                                 '=timeout=%d' % timeout
            ]
            return self._exec_cmd(commands)

    def remove(self, mk_id):
        return self._exec_cmd([
            '/ip/firewall/address-list/remove',
            '=.id=*' + str(mk_id).replace('*', '')
        ])

    def remove_range(self, items):
        ids = [ip.mk_id for ip in items if isinstance(ip, IpAddressListObj)]
        if len(ids) > 0:
            return self._exec_cmd([
                '/ip/firewall/address-list/remove',
                'numbers=' + ','.join(ids)
            ])

    def find(self, ip, list_name):
        if not isinstance(ip, IpStruct):
            raise TypeError
        return self._exec_cmd([
            '/ip/firewall/address-list/print', 'where',
            '?list=%s' % list_name,
            '?address=%s' % str(ip)
        ])

    def read_ips_iter(self, list_name):
        return self._exec_cmd([
            '/ip/firewall/address-list/print', 'where',
            '?list=%s' % list_name
        ])

    def disable(self, user):
        r = IpAddressListManager.find(self, user.ip, LIST_USERS_ALLOWED)
        if len(r) > 1:
            mk_id = r[0]['=.id']
            return self._exec_cmd([
                '/ip/firewall/address-list/disable',
                '=.id=' + str(mk_id),
            ])

    def enable(self, user):
        r = IpAddressListManager.find(self, user.ip, LIST_USERS_ALLOWED)
        if len(r) > 1:
            mk_id = r[0]['=.id']
            return self._exec_cmd([
                '/ip/firewall/address-list/enable',
                '=.id=' + str(mk_id),
            ])


class MikrotikTransmitter(QueueManager, IpAddressListManager):

    def add_user_range(self, user_list):
        super(MikrotikTransmitter, self).add_user_range(user_list)
        for usr in user_list:
            self.add_user(usr)

    def remove_user_range(self, users):
        super(MikrotikTransmitter, self).remove_user_range(users)
        queue_ids = [usr.queue_id for usr in users if usr is not None]
        QueueManager.remove_range(self, queue_ids)
        ips = [user.ip for user in users if isinstance(user, AbonStruct)]
        for ip in ips:
            ip_list_entity = IpAddressListManager.find(self, ip, LIST_USERS_ALLOWED)
            if ip_list_entity is not None and len(ip_list_entity) > 1:
                IpAddressListManager.remove(self, ip_list_entity[0]['=.id'])

    def add_user(self, user, ip_timeout=None):
        super(MikrotikTransmitter, self).add_user(user, ip_timeout)
        if not isinstance(user.ip, IpStruct):
            raise TypeError
        if user.tariff is None or not isinstance(user.tariff, TariffStruct):
            return
        QueueManager.add(self, user)
        IpAddressListManager.add(self, LIST_USERS_ALLOWED, user.ip, ip_timeout)
        # удаляем из списка заблокированных абонентов
        firewall_ip_list_obj = IpAddressListManager.find(self, user.ip, LIST_USERS_BLOCKED)
        if len(firewall_ip_list_obj) > 1:
            IpAddressListManager.remove(self, firewall_ip_list_obj[0]['=.id'])

    def remove_user(self, user):
        super(MikrotikTransmitter, self).remove_user(user)
        QueueManager.remove(self, user)
        firewall_ip_list_obj = IpAddressListManager.find(self, user.ip, LIST_USERS_ALLOWED)
        if firewall_ip_list_obj is not None and len(firewall_ip_list_obj) > 1:
            IpAddressListManager.remove(self, firewall_ip_list_obj[0]['=.id'])

    # обновляем основную инфу абонента
    def update_user(self, user, ip_timeout=None):
        super(MikrotikTransmitter, self).update_user(user, ip_timeout)
        if not isinstance(user.ip, IpStruct):
            raise TypeError

        # ищем ip абонента в списке ip
        find_res = IpAddressListManager.find(self, user.ip, LIST_USERS_ALLOWED)

        if not user.is_active:
            # если не активен - то и обновлять не надо
            # но и выключить на всяк случай надо, а то вдруг был включён
            if len(find_res) > 1:
                # и если найден был - то удалим ip из разрешённых
                IpAddressListManager.remove(self, find_res[0]['=.id'])
            return

        # если нет услуги то её не должно быть и в nas
        if user.tariff is None or not isinstance(user.tariff, TariffStruct):
            queue = QueueManager.find(self, 'uid%d' % user.uid)
            if queue is not None:
                QueueManager.remove(self, user)
            return

        # если не найден (mikrotik возвращает пустой словарь в списке если ничего нет)
        if len(find_res) < 2:
            # добавим запись об абоненте
            IpAddressListManager.add(self, LIST_USERS_ALLOWED, user.ip, ip_timeout)
        else:
            mk_id = find_res[0]['=.id']
            # то обновляем запись в mikrotik
            IpAddressListManager._edit(self, mk_id, ip_timeout)

        # Проверяем шейпер
        queue = QueueManager.find(self, 'uid%d' % user.uid)
        if queue is None:
            QueueManager.add(self, user)
            return
        if queue != user:
            QueueManager.update(self, user)

    def ping(self, host, count=10):
        super(MikrotikTransmitter, self).ping(host)
        r = self._exec_cmd([
            '/ip/arp/print',
            '?address=%s' % host
        ])
        if r == [{}]:
            return
        interface = r[0]['=interface']
        r = self._exec_cmd([
            '/ping', '=address=%s' % host, '=arp-ping=yes', '=interval=100ms', '=count=%d' % count,
                     '=interface=%s' % interface
        ])
        received, sent = int(r[-2:][0]['=received']), int(r[-2:][0]['=sent'])
        return received, sent

    # Тарифы хранить нам не надо, так что методы тарифов ниже не реализуем
    def add_tariff_range(self, tariff_list):
        pass

    # соответственно и удалять тарифы не надо
    def remove_tariff_range(self, tariff_list):
        pass

    # и добавлять тоже
    def add_tariff(self, tariff):
        pass

    # и обновлять
    def update_tariff(self, tariff):
        pass

    def remove_tariff(self, tid):
        pass

    def read_users(self):
        # shapes is ShapeItem
        # allowed_ips = IpAddressListManager.read_ips_iter(self, LIST_USERS_ALLOWED)
        queues = QueueManager.read_queue_iter(self)
        return queues
