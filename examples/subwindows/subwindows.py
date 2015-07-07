import kivy
kivy.require('1.0.9')

from kivy.app import App
from kivy.uix.button import Button
from kivy.core.subwindow import SubWindow

class SubWindowsApp(App):
    def build(self):
        return Button(text='show subwindow', on_press=self.show_popup)

    def show_popup(self, b):
        SubWindow('my subwindow', None, True)

if __name__ == '__main__':
    SubWindowsApp().run()
