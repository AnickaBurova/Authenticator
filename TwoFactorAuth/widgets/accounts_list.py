from gi import require_version
require_version("Gtk", "3.0")
from gi.repository import Gtk, Gio, Gdk, GObject, GLib
from TwoFactorAuth.widgets.confirmation import ConfirmationMessage
from TwoFactorAuth.widgets.account_row import AccountRow
import logging
from gettext import gettext as _
from hashlib import sha256


class AccountsList(Gtk.ListBox):
    scrolled_win = None
    selected_count = 0

    def __init__(self, application, window):
        self.app = application
        self.window = window
        self.generate()
        self.window.connect("key-press-event", self.on_key_press)

    def generate(self):
        Gtk.ListBox.__init__(self)
        # Create a ScrolledWindow for accounts
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        self.get_style_context().add_class("applications-list")
        self.set_adjustment()
        self.set_selection_mode(Gtk.SelectionMode.SINGLE)
        box.pack_start(self, True, True, 0)

        self.scrolled_win = Gtk.ScrolledWindow()
        self.scrolled_win.add_with_viewport(box)

        apps = self.app.db.fetch_apps()
        count = len(apps)

        for app in apps:
            self.add(AccountRow(self, self.window, app))

        if count != 0:
            self.select_row(self.get_row_at_index(0))
        self.show_all()

    def on_key_press(self, app, key_event):
        """
            Keyboard Listener handling
        """
        keyname = Gdk.keyval_name(key_event.keyval).lower()
        if not self.window.is_locked():
            if not self.window.no_account_box.is_visible():
                if keyname == "up" or keyname == "down":
                    count = self.app.db.count()
                    dx = -1 if keyname == "up" else 1
                    selected_row = self.get_selected_row()
                    if selected_row is not None:
                        index = selected_row.get_index()
                        index = (index + dx)%count
                        self.select_row(self.get_row_at_index(index))
                        return True
        return False

    def toggle_select_mode(self):
        pass_enabled = self.app.cfg.read("state", "login")
        is_select_mode = self.window.hb.is_on_select_mode()
        if is_select_mode:
            self.set_selection_mode(Gtk.SelectionMode.MULTIPLE)
        else:
            self.set_selection_mode(Gtk.SelectionMode.SINGLE)

        self.select_row(self.get_row_at_index(0))

        for row in self.get_children():
            checkbox = row.get_checkbox()
            code_label = row.get_code_label()
            visible = checkbox.get_visible()
            selected = checkbox.get_active()
            style_context = code_label.get_style_context()
            if is_select_mode:
                self.select_account(checkbox)
                style_context.add_class("application-secret-code-select-mode")
            else:
                style_context.remove_class(
                    "application-secret-code-select-mode")

            checkbox.set_visible(not visible)
            checkbox.set_no_show_all(visible)

    def append(self,  app):
        """
            Add an element to the ListBox
        """
        app[2] = sha256(app[2].encode('utf-8')).hexdigest()
        self.add(AccountRow(self, self.window, app))
        self.show_all()

    def remove_selected(self, *args):
        """
            Remove selected accounts
        """
        for row in self.get_selected_rows():
            checkbox = row.get_checkbox()
            if checkbox.get_active():
                row.remove()
        self.unselect_all()
        self.toggle_select_mode()
        self.window.refresh_window()

    def select_account(self, checkbutton):
        """
            Select an account
            :param checkbutton:
        """
        is_active = checkbutton.get_active()
        is_visible = checkbutton.get_visible()
        listbox_row = checkbutton.get_parent().get_parent().get_parent()
        if is_active:
            self.select_row(listbox_row)
            if is_visible:
                self.selected_count += 1
        else:
            self.unselect_row(listbox_row)
            if is_visible:
                self.selected_count -= 1
        self.window.hb.remove_button.set_sensitive(self.selected_count > 0)

    def get_selected_row_id(self):
        selected_row = self.get_selected_row()
        if selected_row:
            return selected_row.get_id()
        else:
            return None

    def get_scrolled_win(self):
        return self.scrolled_win

    def toggle(self, visible):
        self.set_visible(visible)
        self.set_no_show_all(not visible)

    def is_visible(self):
        return self.get_visible()

    def hide(self):
        self.toggle(False)

    def show(self):
        self.toggle(True)

    def refresh(self):
        self.scrolled_win.hide()
        self.scrolled_win.show_all()
