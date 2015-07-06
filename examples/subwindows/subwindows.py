import kivy
kivy.require('1.0.9')

from kivy.app import App
from kivy.uix.button import Button

class SubWindowsApp(App):
	def build(self):
		return Button(text='hello world')

if __name__ == '__main__':
	SubWindowsApp().run()
