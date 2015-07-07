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

    def __init__(self, title = 'Untitled', kv_file = None, modal = True):
        self.root = None
        self.window = None
        self.popup = None

        self.title = title
        self.modal = modal

        self._create_subwindow(kv_file)

    def build(self):
        return None

    def _create_subwindow(self, kv_file):
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
        from kivy.uix.subwindow import SubWindow as SubWindowWidget

        return SubWindowWidget(title = self.title, content = self.root, auto_dismiss = False,
                               size_hint=(None, None), size=(400, 300), pos=(20, 20))

    def close(self):
        if self.popup is not None:
            self.popup.dismiss()

        if self.window is not None:
            self.window.close()
