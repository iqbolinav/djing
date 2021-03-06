from typing import Optional, AnyStr

from jsonfield import JSONField
from django.db import models
from django.shortcuts import resolve_url
from django.utils.translation import gettext_lazy as _

from djing.fields import MACAddressField
from djing.lib import MyChoicesAdapter
from group_app.models import Group
from . import dev_types
from .base_intr import DevBase


class DeviceDBException(Exception):
    pass


class DeviceMonitoringException(Exception):
    pass


class Device(models.Model):
    _cached_manager = None

    ip_address = models.GenericIPAddressField(verbose_name=_('Ip address'), null=True, blank=True)
    mac_addr = MACAddressField(verbose_name=_('Mac address'), null=True, blank=True, unique=True)
    comment = models.CharField(_('Comment'), max_length=256)
    DEVICE_TYPES = (
        ('Dl', dev_types.DLinkDevice),
        ('Pn', dev_types.OLTDevice),
        ('On', dev_types.OnuDevice),
        ('Ex', dev_types.EltexSwitch),
        ('Zt', dev_types.Olt_ZTE_C320),
        ('Zo', dev_types.ZteOnuDevice),
        ('Z6', dev_types.ZteF601),
        ('Hw', dev_types.HuaweiSwitch)
    )
    devtype = models.CharField(_('Device type'), max_length=2, default=DEVICE_TYPES[0][0],
                               choices=MyChoicesAdapter(DEVICE_TYPES))
    man_passw = models.CharField(_('SNMP password'), max_length=16, null=True, blank=True)
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('Device group'))
    parent_dev = models.ForeignKey('self', verbose_name=_('Parent device'), blank=True, null=True,
                                   on_delete=models.SET_NULL)

    snmp_extra = models.CharField(_('SNMP extra info'), max_length=256, null=True, blank=True)
    extra_data = JSONField(verbose_name=_('Extra data'),
                           help_text=_('Extra data in JSON format. You may use it for your custom data'),
                           blank=True, null=True)

    NETWORK_STATES = (
        ('und', _('Undefined')),
        ('up', _('Up')),
        ('unr', _('Unreachable')),
        ('dwn', _('Down'))
    )
    status = models.CharField(_('Status'), max_length=3, choices=NETWORK_STATES, default='und')

    is_noticeable = models.BooleanField(_('Send notify when monitoring state changed'), default=False)

    class Meta:
        db_table = 'dev'
        verbose_name = _('Device')
        verbose_name_plural = _('Devices')
        ordering = ('id',)

    def get_manager_klass(self):
        try:
            return next(klass for code, klass in self.DEVICE_TYPES if code == self.devtype)
        except StopIteration:
            raise TypeError('one of types is not subclass of DevBase. '
                            'Or implementation of that device type is not found')

    def get_manager_object(self) -> DevBase:
        man_klass = self.get_manager_klass()
        if self._cached_manager is None:
            self._cached_manager = man_klass(self)
        return self._cached_manager

    # Can attach device to subscriber in subscriber page
    def has_attachable_to_subscriber(self) -> bool:
        mngr = self.get_manager_klass()
        return mngr.has_attachable_to_subscriber

    def __str__(self):
        return "%s: (%s) %s %s" % (self.comment, self.get_devtype_display(), self.ip_address or '', self.mac_addr or '')

    def generate_config_template(self) -> Optional[AnyStr]:
        mng = self.get_manager_object()
        return mng.monitoring_template()

    def register_device(self):
        mng = self.get_manager_object()
        if not self.extra_data:
            if self.parent_dev and self.parent_dev.extra_data:
                return mng.register_device(self.parent_dev.extra_data)
        return mng.register_device(self.extra_data)

    def get_absolute_url(self):
        return resolve_url('devapp:edit', self.group.pk, self.pk)


class Port(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, verbose_name=_('Device'))
    num = models.PositiveSmallIntegerField(_('Number'), default=0)
    descr = models.CharField(_('Description'), max_length=60, null=True, blank=True)

    def __str__(self):
        return "%d: %s" % (self.num, self.descr)

    class Meta:
        db_table = 'dev_port'
        unique_together = ('device', 'num')
        permissions = (
            ('can_toggle_ports', _('Can toggle ports')),
        )
        verbose_name = _('Port')
        verbose_name_plural = _('Ports')
        ordering = ('num',)
