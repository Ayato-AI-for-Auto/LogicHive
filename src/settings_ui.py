import sys
from pathlib import Path

# Ensure src is in path for imports
src_path = str(Path(__file__).parent.resolve())
if src_path not in sys.path:
    sys.path.append(src_path)

import flet as ft

from core.config import (
    CONFIG_SOURCE,
    GEMINI_API_KEY,
    HOST,
    MODEL_TYPE,
    PORT,
    save_config,
)
from core.logging_config import get_logger
from orchestrator import check_integrity

logger = get_logger("settings_ui")

def main(page: ft.Page):
    page.title = "LogicHive Settings & Control"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 30
    page.window_width = 800
    page.window_height = 800
    page.window_resizable = True

    # --- State Variables ---
    config_state = {
        "MODEL_TYPE": MODEL_TYPE,
        "GEMINI_API_KEY": GEMINI_API_KEY or "",
        "HOST": HOST,
        "PORT": str(PORT),
    }

    # --- UI Components ---

    # Header
    header = ft.Row(
        [
            ft.Icon(ft.icons.SECURITY, color=ft.colors.AMBER, size=40),
            ft.Text("LogicHive Dashboard", size=32, weight=ft.FontWeight.BOLD),
        ],
        alignment=ft.MainAxisAlignment.START,
    )

    config_source_text = ft.Text(
        f"Config Source: {CONFIG_SOURCE}", size=12, color=ft.colors.GREY_400
    )

    # Tab 1: General Settings
    provider_dropdown = ft.Dropdown(
        label="AI Provider",
        value=config_state["MODEL_TYPE"],
        options=[
            ft.dropdown.Option("gemini", "Google Gemini (Cloud)"),
            ft.dropdown.Option("ollama", "Ollama (Local)"),
        ],
        on_change=lambda e: update_state("MODEL_TYPE", e.control.value),
    )

    gemini_key_input = ft.TextField(
        label="Gemini API Key",
        value=config_state["GEMINI_API_KEY"],
        password=True,
        can_reveal_password=True,
        on_change=lambda e: update_state("GEMINI_API_KEY", e.control.value),
        width=500,
    )

    host_input = ft.TextField(
        label="Host (127.0.0.1 for local, 0.0.0.0 for LAN)",
        value=config_state["HOST"],
        on_change=lambda e: update_state("HOST", e.control.value),
    )

    port_input = ft.TextField(
        label="Port",
        value=config_state["PORT"],
        on_change=lambda e: update_state("PORT", e.control.value),
    )

    save_button = ft.ElevatedButton(
        "Save Configuration",
        icon=ft.icons.SAVE,
        on_click=lambda _: save_settings(),
        style=ft.ButtonStyle(color=ft.colors.WHITE, bgcolor=ft.colors.BLUE_700),
    )

    # Tab 2: Integrity Check
    integrity_result_area = ft.Column(scroll=ft.ScrollMode.ALWAYS, height=400)

    async def run_integrity_check(_e):
        integrity_result_area.controls.clear()
        integrity_result_area.controls.append(ft.ProgressBar(width=400, color="blue"))
        page.update()
        logger.info("Starting integrity check from UI")

        try:
            report = await check_integrity()
            integrity_result_area.controls.clear()

            status_color = ft.colors.GREEN if report["status"] == "Healthy" else ft.colors.AMBER
            if report["status"] == "Error":
                status_color = ft.colors.RED

            integrity_result_area.controls.append(
                ft.Text(
                    f"Status: {report['status']}",
                    size=20,
                    color=status_color,
                    weight=ft.FontWeight.BOLD,
                )
            )

            for component, details in report["details"].items():
                comp_status = details.get("status", "Unknown")
                comp_color = ft.colors.GREEN if comp_status == "Healthy" else ft.colors.AMBER

                integrity_result_area.controls.append(
                    ft.ExpansionTile(
                        title=ft.Text(f"{component.upper()}: {comp_status}", color=comp_color),
                        subtitle=ft.Text(details.get("message", "")),
                        controls=[
                            ft.Container(
                                content=ft.Text(str(details.get("details", "")), size=12),
                                padding=10,
                                bgcolor=ft.colors.GREY_900,
                                border_radius=5,
                            )
                        ]
                    )
                )
            logger.info(
                "Integrity check completed successfully", extra={"report_status": report["status"]}
            )
        except Exception as ex:
            logger.exception("Integrity check failed with an unexpected error")
            integrity_result_area.controls.clear()
            integrity_result_area.controls.append(ft.Text(f"Error: {ex}", color=ft.colors.RED))

        page.update()

    integrity_button = ft.ElevatedButton(
        "Run Integrity Check",
        icon=ft.icons.HEALTH_AND_SAFETY,
        on_click=run_integrity_check,
    )

    # --- Helper Functions ---

    def update_state(key, value):
        config_state[key] = value

    def save_settings():
        try:
            success = save_config(config_state)
            if success:
                logger.info("Configuration saved successfully from UI")
                page.snack_bar = ft.SnackBar(ft.Text("Configuration saved successfully!"))
                page.snack_bar.open = True
            else:
                logger.error("Failed to save configuration from UI")
                page.snack_bar = ft.SnackBar(
                    ft.Text("Failed to save configuration."), bgcolor=ft.colors.RED
                )
                page.snack_bar.open = True
        except Exception as ex:
            logger.exception("Exception occurred while saving configuration")
            page.snack_bar = ft.SnackBar(
                ft.Text(f"Error saving config: {ex}"), bgcolor=ft.colors.RED
            )
            page.snack_bar.open = True
        page.update()

    # --- Layout ---
    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        tabs=[
            ft.Tab(
                text="Configuration",
                icon=ft.icons.SETTINGS,
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("AI Provider & API Keys", size=20, weight=ft.FontWeight.BOLD),
                            provider_dropdown,
                            gemini_key_input,
                            ft.Divider(),
                            ft.Text("Network Settings", size=20, weight=ft.FontWeight.BOLD),
                            ft.Row([host_input, port_input]),
                            ft.VerticalDivider(),
                            save_button,
                        ],
                        spacing=20,
                    ),
                    padding=20,
                ),
            ),
            ft.Tab(
                text="System Health",
                icon=ft.icons.DASHBOARD,
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                "System Integrity & Diagnostics",
                                size=20,
                                weight=ft.FontWeight.BOLD,
                            ),
                            integrity_button,
                            ft.Divider(),
                            integrity_result_area,
                        ],
                        spacing=20,
                    ),
                    padding=20,
                ),
            ),
        ],
        expand=1,
    )

    page.add(
        header,
        config_source_text,
        ft.Divider(),
        tabs,
    )

if __name__ == "__main__":
    logger.info("Starting LogicHive Settings UI")
    try:
        ft.app(target=main)
    except Exception:
        logger.exception("Fatal error occurred in Settings UI")
        sys.exit(1)
