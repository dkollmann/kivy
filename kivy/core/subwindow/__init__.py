# pylint: disable=W0611
# coding: utf-8
'''
SubWindow
======

Class for creating a subwindow. This means that for desktop applications,
a new window is created. For mobile apps, a popup is used inside the main window.
'''

#__all__ = ('Keyboard', 'WindowBase', 'Window')

from os.path import exists

from kivy import platform
from kivy.logger import Logger
from kivy.lang import Builder
from kivy.resources import resource_find

class SubWindow:
    UseNativeWindow = platform != 'ios' and platform != 'android'

    @staticmethod
    def _getarg(kwargs, key, default):
        if not key in kwargs:
            return default

        return kwargs[key]

    def __init__(self, **kwargs):
        if 'title' not in kwargs:
            kwargs.setdefault('title', 'Untitled')

        if 'size' not in kwargs and not 'size_hint' in kwargs:
            kwargs.setdefault('size', (400, 300))
            kwargs.setdefault('size_hint', (None, None))

        self.root = None
        self.window = None
        self.popup = None

        self._create_subwindow(**kwargs)

    def build(self):
        return None

    def _create_subwindow(self, **kwargs):
        kv_file = SubWindow._getarg(kwargs, 'kv_file', None)

        if not kv_file is None:
            if __debug__:
                Logger.debug('Subwindow: Loading kv <{0}>'.format(kv_file))

            rfilename = resource_find(kv_file)

            if rfilename is None or not exists(rfilename):
                if __debug__:
                    Logger.debug('Subwindow: kv <%s> not found' % kv_file)

                return None

            self.root = Builder.load_file(rfilename)

            root = self.build()

            if not root is None:
                self.root = root

        if SubWindow.UseNativeWindow and SubWindow._getarg(kwargs, 'allowNative', True):
            from kivy.core.window import WindowClass

            self.window = self._create_window(**kwargs)
        else:
            self.popup = self._create_popup(**kwargs)

            self.popup.open()

    def _create_window(self, **kwargs):
        from kivy.core.window import WindowClass

        w = WindowClass(**kwargs)

        w.set_title(self.title)

        w.add_widget(self.root)

        return w

    def _create_popup(self, **kwargs):
        from kivy.uix.subwindow import SubWindow as SubWindowWidget

        return SubWindowWidget(content = self.root, auto_dismiss = False, **kwargs)

    def close(self):
        if self.popup is not None:
            self.popup.dismiss()

        if self.window is not None:
            self.window.close()
