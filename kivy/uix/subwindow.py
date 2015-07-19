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
from kivy.clock import Clock

from kivy.uix.floatmodalview import FloatModalView
from kivy.uix.widget import Widget
from kivy.uix.button import Button

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

    allow_maximize = BooleanProperty(True)
    '''Defines if the window can be maximized. Must be a resizable window.

    :attr:`allow_maximize` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to 'True'.
    '''

    allow_minimize = BooleanProperty(True)
    '''Defines if the window can be minimized. Must be a resizable or fixed window.

    :attr:`allow_minimize` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to 'True'.
    '''

    allow_close = BooleanProperty(True)
    '''Defines if the window has a close button.

    :attr:`allow_close` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to 'True'.
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

        self._maximize()

    # Minimize the window
    def minimize(self):
        if self.minimized:
            return

        self.minimized = True

        self.dispatch('on_minimize', self)

        self._minimize()

    # Restore the window
    def restore(self):
        if self.minimized:
            self.minimized = False

            self.dispatch('on_restore', self, True)

            self._restore(True)

        elif self.maximized:
            self.maximized = False

            self.dispatch('on_restore', self, False)

            self._restore(False)

    # Switch the window between native and popup
    def switch(self):
        self._switch()

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


class SubWindowNative:
    def __init__(self, **kwargs):
        self._created = False
        self._open = False

        from kivy.core.window import WindowClass

        kwargs['subwindow'] = True

        self._win = WindowClass(**kwargs)

        type = kwargs['type']

        if type == 'resizable':
            self._win.resizable = True

        elif type == 'fixed':
            self._win.resizable = False

        elif type == 'tool':
            self._win.resizable = False

        elif type == 'borderless':
            self._win.resizable = False
            self._win.borderless = True

        else:
            raise SubWindowException("Unhandled window type")

        pos = kwargs['pos']

        self._win.position = 'custom'
        self._win.left = pos[0]
        self._win.top  = pos[1]

        self._win.system_size = kwargs['size']

        self._win.title = kwargs['title']

        self._win.initialized = False

    def open(self):
        if self._open:
            return

        if not self._created:
            self._created = True

            self._win.create_window()

            self._win.set_title(self._win.title)

            self._open = True

    def close(self):
        if not self._open:
            return

        self._win.close()


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

    auto_open = BooleanProperty(False)
    '''Defines if the window is shown automatically.

    :attr:`auto_open` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to 'False'.
    '''

    def __init__(self, **kwargs):
        super(SubWindow, self).__init__(**kwargs)

        if 'title' not in kwargs:
            kwargs.setdefault('title', 'Untitled')

        if 'size' not in kwargs and not 'size_hint' in kwargs:
            kwargs.setdefault('size', (400, 300))
            kwargs.setdefault('size_hint', (None, None))

        self.window = None

        Clock.schedule_once(self._post_init)

    def _post_init(self, dt):
        if self.auto_open:
            self.open()

    def add_widget(self, widget, index=0):
        if not isinstance(widget, SubWindowPopup):
            raise SubWindowException("Only SubWindowPopup objects can be added to SubWindow.")

        if not self.popup is None and not self.popup is widget:
            raise SubWindowException("Only one SubWindowPopup object can be added to SubWindow.")

        self.popup = widget

    def remove_widget(self, widget):
        if widget is self.popup:
            self.popup = None

    def _close(self):
        if self.popup is not None:
            self.popup._close()

        if self.window is not None:
            self.window._close()

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
            self.window = self._create_window(**kwargs)
        else:
            self.popup = self._create_popup(**kwargs)

    def on_popup(self, window, value):
        #TODO: The old value of popup needs to have owner set to None

        if value is not None:
            if not isinstance(value, SubWindowPopup):
                raise SubWindowException("Only SubWindowPopup objects can be assigned as a popup.")

            value.owner = self

    def _create_window(self, **kwargs):
        w = SubWindowNative(**kwargs)

        #w.set_title(self.title)

        #w.add_widget(self.content)

        return w

    def _create_popup(self, **kwargs):
        return SubWindowPopup(auto_dismiss = False, **kwargs)

    def open(self):
        # When there is a popup we assume we should use it
        if self.popup is None and self.window is None:
            self._create_subwindow(
                pos = self.pos,
                pos_hint = self.pos_hint,
                size = self.size,
                size_hint = self.size_hint,
                type = self.type,
                title = self.title,
                kv_file = self.kv_file,
                minimized = self.minimized,
                maximized = self.maximized,
                allow_maximize = self.allow_maximize,
                allow_minimize = self.allow_minimize,
                allow_close = self.allow_close,
                content = self.content
            )

        if self.popup is not None:
            self.popup.open()

        if self.window is not None:
            self.window.open()

    def _switch(self):
        #TODO: Add switch code
        pass


class SubWindowPopupButton(Button):
    '''Button class for sub window buttons. Allows you to specify a visibility.

    :Events:
        `update_visible`
            Fired when the visibility of the button is updated.
    '''

    __events__ = ['on_visible']

    def __init__(self, **kwargs):
        super(SubWindowPopupButton, self).__init__(**kwargs)

        self._visible = True

    def setVisible(self, visible):
        self._visible = visible

    def on_visible(self):
        pass


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

    owner = ObjectProperty(None)
    '''The SubWindow class owning this class. May be None. Must be set when created by SubWindow class.

    :attr:`owner` is an :class:`~kivy.properties.ObjectProperty` and defaults
    to None.
    '''

    # Internal properties used for graphical representation.

    _container = ObjectProperty(None)

    _buttons_container = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(SubWindowPopup, self).__init__(**kwargs)

        self._open = False
        self._premax_pos = None
        self._premax_pos_hint = None

        # Collect all the buttons so they are still available when removed
        if self._buttons_container is None:
            raise SubWindowException("The buttons container was not assigned.")

        self._buttons = []

        for b in self._buttons_container.children:
            if isinstance(b, SubWindowPopupButton):
                self._buttons.append(b)

        Clock.schedule_once(self._post_init)

    def _post_init(self, dt):
        self.update_buttons()

    def _remove_button(self, button):
        b = getattr(self, button)

        if b is not None:
            b.parent.remove_widget(b)

            setattr(self, button, None)

    def update_buttons(self):
        # Update all possible buttons
        index = 0
        for b in self._buttons:
            b.dispatch('on_visible')

            # Check if the visibility changed
            if b._visible and not b in self._buttons_container.children:
                self._buttons_container.add_widget(b, index)

            elif not b._visible and b in self._buttons_container.children:
                self._buttons_container.remove_widget(b)

            # Update index
            if b._visible:
                index += 1

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

    def _switch(self):
        if self.owner is not None:
            self.owner._switch()

    def _close(self):
        if not self._open:
            return

        self.dismiss()

    def _maximize(self):
        self._premax_pos = self.pos
        self._premax_pos_hint = self.pos_hint

        self.pos = (0, 0)
        self.pos_hint = {}
        self.size_hint = (1, 1)

        self.update_buttons()

    def _minimize(self):
        #TODO: Add minimize code
        pass

    def _restore(self, wasMinimized):
        if not wasMinimized:
            self.size_hint = (None, None)
            self.pos = self._premax_pos
            self.pos_hint = self._premax_pos_hint

            self.update_buttons()


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
