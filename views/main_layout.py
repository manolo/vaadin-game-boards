"""Application shell layout with sidebar navigation."""

from pyxflow import AppShell, Push, StyleSheet
from pyxflow.components import (
    AppLayout, AppLayoutSection, DrawerToggle,
    H2, HorizontalLayout, SideNav, SideNavItem, Icon,
)
from pyxflow.components.horizontal_layout import Alignment
from pyxflow.menu import get_menu_entries, get_page_header


@AppShell
@Push
@StyleSheet("lumo/lumo.css", "styles/sudoku.css", "styles/chess.css")
class MainLayout(AppLayout):
    def __init__(self):
        # Navbar
        self._page_header = H2("Games")
        self.add_to_navbar(DrawerToggle(), self._page_header)

        # Drawer with SideNav
        header = HorizontalLayout()
        header.add(H2("Games"))
        header.set_default_vertical_component_alignment(Alignment.CENTER)
        header.get_style().set("padding", "10px")

        nav = SideNav()
        for entry in get_menu_entries():
            icon = Icon(entry.icon) if entry.icon else None
            nav.add_item(SideNavItem(entry.title, entry.path, icon))
        self.add_to_drawer(header, nav)

        self.set_primary_section(AppLayoutSection.DRAWER)

    def show_router_layout_content(self, content):
        super().show_router_layout_content(content)
        title = get_page_header(content) or "Games"
        self._page_header.set_text(title)
