# Copyright 2023, by Julien Cegarra & Benoît Valéry. All rights reserved.
# Institut National Universitaire Champollion (Albi, France).
# License : CeCILL, version 2.1 (see the LICENSE file)

import sys
from pyglet import font, image
from pyglet.canvas import get_display
from pyglet.window import Window, key as winkey
from pyglet.graphics import Batch
from pyglet.gl import GL_POLYGON, glLineWidth
from pyglet.text import Label
from pyglet import image, sprite
from core.container import Container
from core.constants import COLORS as C, FONT_SIZES as F, Group as G, PLUGIN_TITLE_HEIGHT_PROPORTION
from core.constants import PATHS as P
from core.constants import REPLAY_MODE, REPLAY_STRIP_PROPORTION
from core.modaldialog import ModalDialog
from core.logger import logger
from core.error import errors
from core.utils import get_conf_value, find_the_last_session_number


class Window(Window):
    def __init__(self, *args, **kwargs):

        errors.win = self

        # Screen definition #
        try:
            screen_index = get_conf_value('Openmatb', 'screen_index')
        except:
            screen_index = 0

        screens = get_display().get_screens()
        if screen_index + 1 > len(screens):
            screen = screens[-1]
            errors.add_error(_(f"In config.ini, the specified screen index exceeds the number of available screens (%s). Last screen selected.") % len(get_display().get_screens()))
        else:
            screen = screens[screen_index]

        self._width=screen.width
        self._height=screen.height
        self._fullscreen=get_conf_value('Openmatb', 'fullscreen')

        super().__init__(fullscreen=self._fullscreen, width=self._width, height=self._height, 
                            vsync=True, *args, **kwargs)

        img_path = P['IMG']
        logo16 = image.load(img_path.joinpath('logo16.png'))
        logo32 = image.load(img_path.joinpath('logo32.png'))
        self.set_icon(logo16, logo32)

        self.set_size_and_location() # Postpone multiple monitor support
        self.set_mouse_visible(REPLAY_MODE)

        self.batch = Batch()
        self.keyboard = dict() # Reproduce a simple KeyStateHandler

        self.create_MATB_background()
        self.alive = True
        self.modal_dialog = None
        self.slider_visible = False

        self.on_key_press_replay = None # used by the replay

        # Display the session ID if need be, at window instanciation
        if REPLAY_MODE == True:
            if len(sys.argv) > 2:
                replay_session_id = int(sys.argv[2])
            else:
                replay_session_id = find_the_last_session_number()
            msg = _('Replay session ID: %s') % replay_session_id
            self.modal_dialog = ModalDialog(self, msg, title='OpenMATB replay')
            
        elif get_conf_value('Openmatb', 'display_session_number'):
            msg = _('Session ID: %s') % logger.session_id
            self.modal_dialog = ModalDialog(self, msg, title='OpenMATB')


    def set_size_and_location(self):
        self.switch_to()        # The Window must be active before setting the location
        target_x = (self.screen.x + self.screen.width / 2) - self.screen.width / 2
        target_y = (self.screen.y + self.screen.height / 2) - self.screen.height / 2
        self.set_location(int(target_x), int(target_y))


    def create_MATB_background(self):
        MATB_container = self.get_container('fullscreen')
        l, b, w, h = MATB_container.get_lbwh()
        container_title_h = PLUGIN_TITLE_HEIGHT_PROPORTION/2

        # Main background
        self.batch.add(4, GL_POLYGON, G(-1), ('v2f/static', (l, b+h, l+w, b+h, l+w, b, l, b)),
                                            ('c4B', C['BACKGROUND'] * 4))

        # Upper band
        self.batch.add(4, GL_POLYGON, G(-1),
                  ('v2f/static', (l, b+h, l+w, b+h,
                                  l+w, b+h*(1-container_title_h), l, b+h*(1-container_title_h))),
                  ('c4B/static', C['BLACK'] * 4))

        # Middle band
        self.batch.add(4, GL_POLYGON, G(0),
                  ('v2f/static', (l,   b + h/2,   l+w, b + h/2,
                                  l+w, b + h*(0.5-container_title_h),
                                  0,   b + h*(0.5-container_title_h))),
                  ('c4B/static', C['BLACK'] * 4))


    def on_draw(self):
        self.set_mouse_visible(self.is_mouse_necessary())
        self.clear()
        self.batch.draw()


    def is_mouse_necessary(self):
        return self.slider_visible == True or REPLAY_MODE == True


    # Log any keyboard input, either plugins accept it or not
    def on_key_press(self, symbol, modifiers):
        if self.modal_dialog is None:
            keystr = winkey.symbol_string(symbol)
            self.keyboard[keystr] = True  # KeyStateHandler

            if keystr == 'ESCAPE':
                self.exit_prompt()
            elif keystr == 'P':
                self.pause_prompt()

            if REPLAY_MODE:
                if self.on_key_press_replay != None:
                    self.on_key_press_replay(symbol, modifiers)
                return

            logger.record_input('keyboard', keystr, 'press')


    def on_key_release(self, symbol, modifiers):
        if self.modal_dialog is not None:
            self.modal_dialog.on_key_release(symbol, modifiers)
            return

        keystr = winkey.symbol_string(symbol)
        self.keyboard[keystr] = False  # KeyStateHandler
        logger.record_input('keyboard', keystr, 'release')


    def exit_prompt(self):
        self.modal_dialog = ModalDialog(self, _('You hit the Escape key'), title=_('Exit OpenMATB?'), exit_key='q')


    def pause_prompt(self):
        self.modal_dialog = ModalDialog(self, _('Pause'))


    def exit(self):
        self.alive = False


    def on_joyaxis_motion(self, joystick, axis, value):
        logger.record_input('joystick', axis, value)


    def get_container_list(self):
        mar = REPLAY_STRIP_PROPORTION if REPLAY_MODE else 0
        w, h = (1-mar) * self.width, (1-mar)*self.height
        b = self.height*mar

        # Vertical bounds
        x1, x2 = (int(w * bound) for bound in [0.35, 0.85])  # Top row
        x3, x4 = (int(w * bound) for bound in [0.30, 0.85])  # Bottom row

        # Horizontal bound
        y1 = b + h/2

        return [Container('invisible', 0, 0, 0, 0),
                Container('fullscreen', 0, b, w, h),
                Container('topleft', 0, y1, x1, h/2),
                Container('topmid', x1, y1, x2 - x1, h/2),
                Container('topright', x2, y1, w-x2, h/2),
                Container('bottomleft', 0, b, x3, h/2),
                Container('bottommid', x3, b, x4 - x3, h/2),
                Container('bottomright', x4, b, w - x4, h/2),
                Container('mediastrip', 0, 0, self._width*(1+mar), b),
                Container('inputstrip', w, b, self._width*mar, h)]


    def get_container(self, placement_name):
        container = [c for c in self.get_container_list() if c.name == placement_name]
        if len(container) > 0:
            return container[0]
        else:
            print(_('Error. No placement found for the [%s] alias') % placement_name)
