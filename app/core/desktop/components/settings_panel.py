from PySide6.QtWidgets import QWidget, QPushButton, QComboBox, QCheckBox, QSpinBox, QSlider, QLineEdit
from app.core.desktop.components.widget_factory.layout_builder import LayoutBuilderFactory
from app.core.desktop.components.widget_factory.basic_widgets import BasicWidgetFactory
from app.core.desktop.components.widget_factory.complex_widgets import ComplexWidgetFactory
from app.core.desktop.components.widget_factory.specialized_widgets import SpecializedWidgetFactory

class WidgetBuildersMixin:
    @property
    def layout_builder(self):
        if not hasattr(self, '_layout_builder_obj'):
            self._layout_builder_obj = LayoutBuilderFactory(self)
        return self._layout_builder_obj

    @property
    def basic_widgets(self):
        if not hasattr(self, '_basic_widgets_obj'):
            self._basic_widgets_obj = BasicWidgetFactory(self)
        return self._basic_widgets_obj

    @property
    def complex_widgets(self):
        if not hasattr(self, '_complex_widgets_obj'):
            self._complex_widgets_obj = ComplexWidgetFactory(self)
        return self._complex_widgets_obj

    @property
    def specialized_widgets(self):
        if not hasattr(self, '_specialized_widgets_obj'):
            self._specialized_widgets_obj = SpecializedWidgetFactory(self)
        return self._specialized_widgets_obj

    # --- Layout Builder Delegates ---
    def _build_dynamic_tab_content(self, tab_name: str, settings_list: list) -> QWidget:
        return self.layout_builder.build_dynamic_tab_content(tab_name, settings_list)

    def _create_setting_row(self, info: dict, context_key: str | None = None) -> QWidget:
        return self.layout_builder.create_setting_row(info, context_key)

    def _setup_dynamic_action_buttons(self, key: str, combo_box, right_layout):
        return self.layout_builder.setup_dynamic_action_buttons(key, combo_box, right_layout)

    def _rebuild_settings_tab(self):
        return self.layout_builder.rebuild_settings_tab()

    def _populate_all_tabs(self):
        return self.layout_builder.populate_all_tabs()

    def _update_translator_tooltip(self, translator_name: str):
        return self.layout_builder.update_translator_tooltip(translator_name)

    def _handle_widget_button_click(self, key: str, associated_widget: QWidget):
        return self.layout_builder.handle_widget_button_click(key, associated_widget)

    def _create_bottom_panel(self) -> QWidget:
        return self.layout_builder.create_bottom_panel()

    def _create_font_scale_widget(self) -> QWidget:
        return self.layout_builder.create_font_scale_widget()

    def _create_theme_manager_widget(self) -> QWidget:
        return self.layout_builder.create_theme_manager_widget()

    def _create_preview_tester_tab(self) -> QWidget:
        return self.layout_builder.create_preview_tester_tab()

    # --- Basic Widgets Delegates ---
    def _create_checkbox(self, info: dict) -> QCheckBox:
        return self.basic_widgets.create_checkbox(info)

    def _create_slider(self, info: dict) -> QWidget:
        return self.basic_widgets.create_slider(info)

    def _create_spinbox(self, info: dict) -> QSpinBox:
        return self.basic_widgets.create_spinbox(info)

    def _create_entry(self, info: dict) -> QLineEdit:
        return self.basic_widgets.create_entry(info)

    def _create_entry_with_button(self, info: dict) -> QWidget:
        return self.basic_widgets.create_entry_with_button(info)

    def _create_open_yaml_button(self, info: dict) -> QPushButton:
        return self.basic_widgets.create_open_yaml_button(info)

    # --- Complex Widgets Delegates ---
    def _create_segmented_button(self, info: dict) -> QWidget:
        return self.complex_widgets.create_segmented_button(info)

    def _set_combobox_value_by_data(self, combo_box, value):
        return self.complex_widgets.set_combobox_value_by_data(combo_box, value)

    def _create_combobox(self, info: dict) -> QComboBox:
        return self.complex_widgets.create_combobox(info)

    def _create_grid_segmented_button(self, info: dict) -> QWidget:
        return self.complex_widgets.create_grid_segmented_button(info)

    # --- Specialized Widgets Delegates ---
    def _create_api_profile_selector(self, info: dict) -> QWidget:
        return self.specialized_widgets.create_api_profile_selector(info)

    def _create_pool_profile_selector(self, info: dict) -> QWidget:
        return self.specialized_widgets.create_pool_profile_selector(info)

    def _create_ai_model_selector(self, info: dict) -> QWidget:
        return self.specialized_widgets.create_ai_model_selector(info)

    def _create_api_manager_widget(self, info: dict) -> QWidget:
        return self.specialized_widgets.create_api_manager_widget(info)

    def _create_font_combobox(self, info: dict) -> QWidget:
        return self.specialized_widgets.create_font_combobox(info)

    def _style_custom_fonts_in_combobox(self, combo_box: QComboBox):
        return self.specialized_widgets.style_custom_fonts_in_combobox(combo_box)

    def _get_themed_arrow_icon_path(self, color_hex: str, theme_name: str) -> str:
        return self.specialized_widgets.get_themed_arrow_icon_path(color_hex, theme_name)

    def _create_translator_chain_builder(self, info: dict) -> QWidget:
        return self.specialized_widgets.create_translator_chain_builder(info)

    def _create_chain_step_widget(self) -> QWidget:
        return self.specialized_widgets.create_chain_step_widget()

    def _add_chain_step(self):
        return self.specialized_widgets.add_chain_step()

    def _remove_chain_step(self):
        return self.specialized_widgets.remove_chain_step()

    def _get_translator_chain_string(self) -> str:
        return self.specialized_widgets.get_translator_chain_string()

    def _rebuild_chain_from_string(self, chain_string: str):
        return self.specialized_widgets.rebuild_chain_from_string(chain_string)

    def _update_chain_ui_state(self):
        return self.specialized_widgets.update_chain_ui_state()

    def _update_chain_list_height(self):
        return self.specialized_widgets.update_chain_list_height()
