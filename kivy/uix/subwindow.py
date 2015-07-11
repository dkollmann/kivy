'''
SubWindow
=====

.. image:: images/subwindow.jpg
    :align: right

The :class:`SubWindow` widget is used to create modal subwindows. By default, the subwindow
will cover the whole "parent" window. When you are creating a subwindow, you
must at least set a :attr:`SubWindow.title` and :attr:`SubWindow.content`.

Remember that the default size of a Widget is size_hint=(1, 1). If you don't
want your subwindow to be fullscreen, either use size hints with values less than 1
(for instance size_hint=(.8, .8)) or deactivate the size_hint and use
fixed size attributes.


Examples
--------

Example of a simple 400x400 Hello world subwindow::

    subwindow = SubWindow(title='Test subwindow',
        content=Label(text='Hello world'),
        size_hint=(None, None), size=(400, 400))

By default, any click outside the subwindow will dismiss/close it. If you don't
want that, you can set
:attr:`~kivy.uix.modalview.ModalView.auto_dismiss` to False::

    subwindow = SubWindow(title='Test subwindow', content=Label(text='Hello world'),
                  auto_dismiss=False)
    subwindow.open()

To manually dismiss/close the subwindow, use
:attr:`~kivy.uix.modalview.ModalView.dismiss`::

    subwindow.close()

Both :meth:`~kivy.uix.modalview.ModalView.open` and
:meth:`~kivy.uix.modalview.ModalView.dismiss` are bindable. That means you
can directly bind the function to an action, e.g. to a button's on_press::

    # create content and add to the subwindow
    content = Button(text='Close me!')
    subwindow = SubWindow(content=content, auto_dismiss=False)

    # bind the on_press event of the button to the dismiss function
    content.bind(on_press=subwindow.dismiss)

    # open the subwindow
    subwindow.open()


SubWindow Events
------------

There are two events available: `on_open` which is raised when the subwindow is
opening, and `on_dismiss` which is raised when the subwindow is closed.
For `on_dismiss`, you can prevent the
subwindow from closing by explictly returning True from your callback::

    def my_callback(instance):
        print('SubWindow', instance, 'is being dismissed but is prevented!')
        return True
    subwindow = SubWindow(content=Label(text='Hello world'))
    subwindow.bind(on_close=my_callback)
    subwindow.open()

'''

__all__ = ('SubWindowPopup', 'SubWindow')

from os.path import exists

from kivy import platform
from kivy.logger import Logger
from kivy.lang import Builder
from kivy.resources import resource_find
from kivy.core.window import WindowClass

from kivy.uix.floatmodalview import FloatModalView
from kivy.uix.widget import Widget

from kivy.properties import (StringProperty, ObjectProperty, OptionProperty,
                             NumericProperty, ListProperty, BooleanProperty)


class SubWindowException(Exception):
    '''SubWindow exception, fired when multiple content widgets are added to the
    subwindow.
    '''


class SubWindowRequestCloseEvent:
    def __init__(self, force):
        # This attribute is set to tell the event dispatcher if it is okay to close the window or not
        self.mayClose = True

        # If this is true, the value of mayClose will not matter and the window will close anyway
        self.forceClose = force


class SubWindowBase:
    '''SubWindowBase class. It provides the attributes for both the SubWindow and the SubWindowPopup class.

    :Events:
        `on_request_close`
            Fired when the user or code tries to close the window.
            `window` The window firing the event.
            `data`   The SubWindowRequestCloseEvent data.

        `on_close`
            Fired when the window is closed.
            `window` The window firing the event.

        `on_maximize`
            Fired when the window is maximized.
            `window` The window firing the event.

        `on_minimize`
            Fired when the window is minimized.
            `window` The window firing the event.

        `on_restore`
            Fired when the window is restore.
            `window` The window firing the event.
            `wasMinimized` Stores if the window was restored from being minimized or maximized.
    '''

    __events__ = ['on_request_close', 'on_close', 'on_maximize', 'on_minimize', 'on_restore']

    type = OptionProperty('resizable', options=['resizable', 'fixed', 'tool', 'borderless'])
    '''The type of window to be created.

    :attr:`type` is a :class:`~kivy.properties.OptionProperty` and
    defaults to 'resizable'. Available options are resizable, fixed, tool and borderless.
    '''

    title = StringProperty('No title')
    '''String that represents the title of the subwindow.

    :attr:`title` is a :class:`~kivy.properties.StringProperty` and defaults to
    'No title'.
    '''

    kv_file = StringProperty('')
    '''String that holds the path to the kv file to be loaded.

    :attr:`kv_file` is a :class:`~kivy.properties.StringProperty` and defaults to
    ''.
    '''

    minimized = BooleanProperty(False)
    '''Stores if the window is minimzed.

    :attr:`minimized` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to 'False'.
    '''

    maximized = BooleanProperty(False)
    '''Stores if the window is maximized.

    :attr:`maximized` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to 'False'.
    '''

    content = ObjectProperty(None)
    '''Content of the subwindow that is displayed just under the title.

    :attr:`content` is an :class:`~kivy.properties.ObjectProperty` and defaults
    to None.
    '''

    def __init__(self, **kwargs):
        pass

    def _close(self):
        # This must close the window
        assert False

    def _onSwitch(self):
        # Must handle the switch
        assert False

    # Try to close the window
    def close(self, force = False):
        e = SubWindowRequestCloseEvent(force)

        self.dispatch('on_request_close', self, e)

        if force or e.mayClose:
            self.dispatch('on_close', self)

            self._close()

    # Maximize the window
    def maximize(self):
        if self.maximized:
            return

        self.maximized = True

        self.dispatch('on_maximize', self)

    def on_maximized(self, window, value):
        a = 0

    # Minimize the window
    def minimize(self):
        if self.minimized:
            return

        self.minimized = True

        self.dispatch('on_minimize', self)

    # Restore the window
    def restore(self):
        if self.minimized:
            self.minimized = False

            self.dispatch('on_restore', self, True)

        elif self.maximized:
            self.maximized = False

            self.dispatch('on_restore', self, False)

    def on_request_close(self, window, event):
        return True

    def on_close(self, window):
        pass

    def on_maximize(self, window):
        pass

    def on_minimize(self, window):
        pass

    def on_restore(self, window, wasMinimized):
        pass


class SubWindowNative(WindowClass):
    pass


class SubWindow(Widget, SubWindowBase):
    '''SubWindow class. It will create a kivy.uix.SubWindow or a native window as required.
    '''

    UseNativeWindow = platform != 'ios' and platform != 'android'

    allow_native = BooleanProperty(True)
    '''Defines if a native window may be created or if it should always be a popup.

    :attr:`allow_native` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to 'True'.
    '''

    allow_switch = BooleanProperty(True)
    '''Defines if the window can be switched being native and popup through an additional button.

    :attr:`allow_switch` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to 'True'.
    '''

    popup = ObjectProperty(None)
    '''SubWindowPopup when not using a native window.

    :attr:`popup` is an :class:`~kivy.properties.ObjectProperty` and defaults
    to None.
    '''

    @staticmethod
    def _getarg(kwargs, key, default):
        if not key in kwargs:
            return default

        return kwargs[key]

    def __init__(self, **kwargs):
        super(SubWindow, self).__init__(**kwargs)

        if 'title' not in kwargs:
            kwargs.setdefault('title', 'Untitled')

        if 'size' not in kwargs and not 'size_hint' in kwargs:
            kwargs.setdefault('size', (400, 300))
            kwargs.setdefault('size_hint', (None, None))

        self.window = None

        if self.popup is None:
            self._create_subwindow(**kwargs)

    def add_widget(self, widget, index=0, canvas=None):
        super(SubWindow, self).add_widget(widget, index, canvas)

        if not isinstance(widget, SubWindowPopup):
            raise SubWindowException("Only one SubWindowPopup object can be added to SubWindow.")

        if not self.popup is None and not self.popup is widget:
            raise SubWindowException("Only one SubWindowPopup object can be added to SubWindow.")

        self.popup = widget

    def remove_widget(self, widget):
        super(SubWindow, self).remove_widget(widget)

        if widget is self.popup:
            self.popup = None

    def on_popup(self, window, value):
        self.clear_widgets()

        if value is not None:
            self.add_widget(value)

    def _close(self):
        if self.popup is not None:
            self.popup.dismiss()

        if self.window is not None:
            self.window.close()

    def _onSwitch(self):
        pass

    def build(self):
        return None

    def _create_subwindow(self, **kwargs):
        if self.content is None:
            if len(self.kv_file) > 0:
                if __debug__:
                    Logger.debug('Subwindow: Loading kv <{0}>'.format(self.kv_file))

                rfilename = resource_find(self.kv_file)

                if rfilename is None or not exists(rfilename):
                    if __debug__:
                        Logger.debug('Subwindow: kv <%s> not found' % self.kv_file)

                    return None

                self.content = Builder.load_file(rfilename)

                content = self.build()

                if not content is None:
                    self.content = content

        if SubWindow.UseNativeWindow and self.allow_native:
            from kivy.core.window import WindowClass

            self.window = self._create_window(**kwargs)
        else:
            self.popup = self._create_popup(**kwargs)

            self.popup.open()

    def _create_window(self, **kwargs):
        w = SubWindowNative(**kwargs)

        w.set_title(self.title)

        w.add_widget(self.content)

        return w

    def _create_popup(self, **kwargs):
        return SubWindowPopup(content = self.content, auto_dismiss = False, **kwargs)

class SubWindowPopup(FloatModalView, SubWindowBase):
    '''SubWindowPopup class. See module documentation for more information.
    '''

    title_size = NumericProperty('14sp')
    '''Represents the font size of the subwindow title.

    :attr:`title_size` is a :class:`~kivy.properties.NumericProperty` and
    defaults to '14sp'.
    '''

    title_align = OptionProperty('center',
                                 options=['left', 'center', 'right', 'justify'])
    '''Horizontal alignment of the title.

    :attr:`title_align` is a :class:`~kivy.properties.OptionProperty` and
    defaults to 'center'. Available options are left, center, right and justify.
    '''

    title_font = StringProperty('DroidSans')
    '''Font used to render the title text.

    :attr:`title_font` is a :class:`~kivy.properties.StringProperty` and
    defaults to 'DroidSans'.
    '''

    title_color = ListProperty([1, 1, 1, 1])
    '''Color used by the Title.

    :attr:`title_color` is a :class:`~kivy.properties.ListProperty` and
    defaults to [1, 1, 1, 1].
    '''

    button_image_source = StringProperty('atlas://data/images/subwindows/')
    '''The path to the images of the subwindow buttons.

    :attr:`button_image_source` is a :class:`~kivy.properties.StringProperty` and
    defaults to 'atlas://data/images/subwindows/'.
    '''

    button_size = NumericProperty('16dp')
    '''Represents the button size of the subwindow for the maximize, minimize, restore and close button.

    :attr:`button_size` is a :class:`~kivy.properties.NumericProperty` and
    defaults to '16dp'.
    '''

    button_spacing = NumericProperty('4dp')
    '''Represents the spacing between the buttons of the subwindow for the maximize, minimize, restore and close button.

    :attr:`button_spacing` is a :class:`~kivy.properties.NumericProperty` and
    defaults to '4dp'.
    '''

    button_align = OptionProperty('right',
                                 options=['left', 'right'])
    '''Horizontal alignment of the buttons.

    :attr:`button_align` is a :class:`~kivy.properties.OptionProperty` and
    defaults to 'right'. Available options are left and right.
    '''

    separator_color = ListProperty([47 / 255., 167 / 255., 212 / 255., 1.])
    '''Color used by the separator between title and content.

    :attr:`separator_color` is a :class:`~kivy.properties.ListProperty` and
    defaults to [47 / 255., 167 / 255., 212 / 255., 1.]
    '''

    separator_height = NumericProperty('2dp')
    '''Height of the separator.

    :attr:`separator_height` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 2dp.
    '''

    # Internal properties used for graphical representation.

    _container = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(SubWindowPopup, self).__init__(**kwargs)

    def _close(self):
        self.dismiss()

    def _onSwitch(self):
        pass

    def add_widget(self, widget):
        if self._container:
            if self.content:
                raise SubWindowException(
                    'SubWindow can have only one widget as content')
            self.content = widget
        else:
            super(SubWindowPopup, self).add_widget(widget)

    def on_content(self, instance, value):
        if self._container:
            self._container.clear_widgets()
            self._container.add_widget(value)

    def on__container(self, instance, value):
        if value is None or self.content is None:
            return
        self._container.clear_widgets()
        self._container.add_widget(self.content)

    def on_touch_down(self, touch):
        if self.disabled and self.collide_point(*touch.pos):
            return True
        return super(SubWindowPopup, self).on_touch_down(touch)

    # Handle when the close button was pressed
    def _onClose(self):
        self.close()

    # Handle when the maximize button was pressed
    def _onMaximize(self):
        self.maximize()

    # Handle when the minimize button was pressed
    def _onMinimize(self):
        self.minimize()

    # Handle when the restore button was pressed
    def _onRestore(self):
        self.restore()


if __name__ == '__main__':
    from kivy.base import runTouchApp
    from kivy.uix.button import Button
    from kivy.uix.label import Label
    from kivy.uix.gridlayout import GridLayout
    from kivy.core.window import Window

    # add subwindow
    content = GridLayout(cols=1)
    content_cancel = Button(text='Cancel', size_hint_y=None, height=40)
    content.add_widget(Label(text='This is a hello world'))
    content.add_widget(content_cancel)
    subwindow = SubWindow(title='Test subwindow',
                  size_hint=(None, None), size=(256, 256),
                  content=content, disabled=True)
    content_cancel.bind(on_release=subwindow.dismiss)

    layout = GridLayout(cols=3)
    for x in range(9):
        btn = Button(text=str(x))
        btn.bind(on_release=subwindow.open)
        layout.add_widget(btn)

    Window.add_widget(layout)

    subwindow.open()

    runTouchApp()
