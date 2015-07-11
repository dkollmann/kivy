import kivy
kivy.require('1.0.9')

from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.subwindow import SubWindow

class SubWindowsApp(App):
    def build(self):
        return Button(text='show subwindow', on_press=self.show_popup)

    def show_popup(self, b):
        SubWindow(title='my subwindow', pos=(50, 50), allow_native=False)

if __name__ == '__main__':
    SubWindowsApp().run()
