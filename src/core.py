""" The entrypoint - core methods and classes"""
import sys

import pystray as ps
from PIL import Image

from src import logger
from src import ui, exceptions
from src.logger import Logger
from src.processing import processing, storage


class SystemTray:
    """ The system stray, the main entry point.
    """

    def __init__(self):
        """ Initialize
        """
        super().__init__()

        # Interface, saves references of important objects
        # ** Add new references in its init (at the end to avoid not created attributes) ! **
        self.interface = {"SystemTray": self}

        # UI
        self.root_thread = ui.RootThread(self.interface)

        # Processing
        self.processing_thread = processing.ProcessingThread(self.interface)

        # Tray
        self.tray = None
        self.icon_image = Image.open(storage.find_file("logo.ico", meipass=True))

        # For actions
        self.states = {
            "Enabled": False
        }
        self.actions = {
            "Open Window": self.open_root,
            "Enabled": self.start_button,
            "Exit": self.stop_tray
        }

        # Set up logger
        logger.Logger.init(self.interface)

    def start_button(self):
        """ Like the root start_button
        """
        if "ProcessingThread" in self.interface and "Root" in self.interface:
            if self.interface["Root"].rendered:

                self.interface["ProcessingThread"].queue.append(
                    {"cmd": "start_button_handle", "params": [None], "kwargs": {}}
                )

    def action(self, icon, item):
        """ Do a action based on item
        :param icon: the icon
        :param item: the item
        """
        self.actions[item.text]()

    def action_check(self, icon, item):
        """ Update check actions
        :param icon: the icon
        :param item: the item
        """
        self.states[item.text] = not item.checked

    def void(self, icon, item):
        """ Do nothing
        :param icon: the icon
        :param item: the item
        """
        pass

    def stop_tray(self, *args, **kwargs):
        """ Stop the tray
        """
        self.tray.visible = False
        self.tray.stop()

    def open_root(self):
        """ Open a window of the root
        """
        self.root_thread.root.deiconify()

    def run(self) -> None:
        """ Start everything because the tray controls most of the components
        """
        self.tray = ps.Icon("FOV Changer", icon=self.icon_image, title="FOV Changer", menu=ps.Menu(
            ps.MenuItem("FOV Changer", self.void, enabled=False),
            ps.Menu.SEPARATOR,
            ps.MenuItem("Open Window", self.action),
            ps.MenuItem("Enabled", self.action, checked=lambda item: self.states["Enabled"]),
            ps.Menu.SEPARATOR,
            ps.MenuItem("Exit", self.action)
        ))

        # Start GUI
        self.root_thread.start()

        # Start Processing stuff
        self.processing_thread.start()

        # Start tray
        Logger.log("System Tray", add=True)
        self.tray.run()
        Logger.log("System Tray", add=False)

        self.on_shutdown()

    def on_shutdown(self):
        """ Will get executed when the tray stops
        """
        # Stop processing
        self.processing_thread.running = False

        # Stop the GUI
        try:
            self.root_thread.root.deiconify()
            self.root_thread.root.quit()
            self.root_thread.join()

        except RuntimeError:
            sys.exit(0)

        # Save storage
        self.interface["Storage"].update_file()