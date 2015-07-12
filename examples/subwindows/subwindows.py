import kivy
kivy.require('1.0.9')

from kivy.app import App
from kivy.uix.subwindow import SubWindow

class SubWindowsApp(App):
    def show_subwindow(self, button):
        pass

if __name__ == '__main__':
    SubWindowsApp().run()
