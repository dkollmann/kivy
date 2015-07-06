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
    UseNativeWindow = platform != 'ios' and platform != 'android' and False

    def __init__(self):
        self.root = None
        self.window = None
        self.popup = None

        self.title = 'Untitled'

    def build(self):
        return None

    def _create_subwindow(self, title, kv_file = None):
        self.title = title

        if not kv_file is None:
            Logger.debug('Subwindow: Loading kv <{0}>'.format(kv_file))

            rfilename = resource_find(kv_file)

            if rfilename is None or not exists(rfilename):
                Logger.debug('Subwindow: kv <%s> not found' % kv_file)
                return None

            self.root = Builder.load_file(rfilename)

            root = self.build()

            if not root is None:
                self.root = root

        if SubWindow.UseNativeWindow:
            from kivy.core.window import WindowClass

            self.window = self._create_window()
        else:
            self.popup = self._create_popup()

            self.popup.open()

    def _create_window(self):
        from kivy.core.window import WindowClass

        w = WindowClass()

        w.set_title(self.title)

        w.add_widget(self.root)

        return w

    def _create_popup(self):
        from kivy.uix.popup import Popup

        return Popup(title = self.title, content = self.root, auto_dismiss = False)

    def close(self):
        if self.popup is not None:
            self.popup.dismiss()

        if self.window is not None:
            self.window.close()
