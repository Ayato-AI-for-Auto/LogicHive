import sys
from pathlib import Path

import flet as ft

# Ensure src is in path for imports
src_path = str(Path(__file__).parent.resolve())
if src_path not in sys.path:
    sys.path.append(src_path)

from core.config import (  # noqa: E402
    CONFIG_SOURCE,
    GEMINI_API_KEY,
    HOST,
    MODEL_TYPE,
    PORT,
    save_config,
)
from core.logging_config import get_logger  # noqa: E402
from orchestrator import check_integrity  # noqa: E402

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
            ft.Icon(ft.Icons.SHIELD, color=ft.Colors.AMBER, size=40),
            ft.Text("LogicHive Dashboard", size=32, weight=ft.FontWeight.BOLD),
        ],
        alignment=ft.MainAxisAlignment.START,
    )

    config_source_text = ft.Text(
        f"Config Source: {CONFIG_SOURCE}", size=12, color=ft.Colors.GREY_400
    )

    # Tab 1: General Settings
    provider_dropdown = ft.Dropdown(
        label="AI Provider",
        value=config_state["MODEL_TYPE"],
        options=[
            ft.dropdown.Option("gemini", "Google Gemini (Cloud)"),
            ft.dropdown.Option("ollama", "Ollama (Local)"),
        ],
        on_select=lambda e: update_state("MODEL_TYPE", e.control.value),
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
        icon=ft.Icons.SAVE,
        on_click=lambda _: save_settings(),
        style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=ft.Colors.BLUE_700),
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

            status_color = (
                ft.Colors.GREEN if report["status"] == "Healthy" else ft.Colors.AMBER
            )
            if report["status"] == "Error":
                status_color = ft.Colors.RED

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
                comp_color = (
                    ft.Colors.GREEN if comp_status == "Healthy" else ft.Colors.AMBER
                )

                integrity_result_area.controls.append(
                    ft.ExpansionTile(
                        title=ft.Text(
                            f"{component.upper()}: {comp_status}", color=comp_color
                        ),
                        subtitle=ft.Text(details.get("message", "")),
                        controls=[
                            ft.Container(
                                content=ft.Text(
                                    str(details.get("details", "")), size=12
                                ),
                                padding=10,
                                bgcolor=ft.Colors.GREY_900,
                                border_radius=5,
                            )
                        ]
                    )
                )
            logger.info(
                "Integrity check completed successfully",
                extra={"report_status": report["status"]}
            )
        except Exception as ex:
            logger.exception("Integrity check failed with an unexpected error")
            integrity_result_area.controls.clear()
            integrity_result_area.controls.append(
                ft.Text(f"Error: {ex}", color=ft.Colors.RED)
            )

        page.update()

    integrity_button = ft.ElevatedButton(
        "Run Integrity Check",
        icon=ft.Icons.HEALTH_AND_SAFETY,
        on_click=run_integrity_check,
    )

    # --- Helper Functions ---

    def get_client_json():
        import json
        data = {
            "mcpServers": {
                "logichive": {
                    "url": f"http://{config_state['HOST']}:{config_state['PORT']}/sse"
                }
            }
        }
        return json.dumps(data, indent=2)

    client_json_field = ft.TextField(
        value=get_client_json(),
        read_only=True,
        multiline=True,
        min_lines=8,
        max_lines=8,
        text_style=ft.TextStyle(font_family="Consolas"),
        expand=True
    )

    def copy_client_json(_):
        page.clipboard.set(get_client_json())
        page.snack_bar = ft.SnackBar(ft.Text("Copied to clipboard!"))
        page.snack_bar.open = True
        page.update()

    copy_button = ft.IconButton(
        icon=ft.Icons.COPY,
        on_click=copy_client_json,
        tooltip="Copy JSON"
    )

    client_setup_section = ft.Column([
        ft.Text(
            "Client Setup (Cline / Custom SSE Client)", size=18, weight=ft.FontWeight.BOLD
        ),
        ft.Text(
            "Copy and paste this into your client's MCP settings file:",
            size=14,
            color=ft.Colors.GREY_400,
        ),
        ft.Row(
            [client_json_field, copy_button],
            vertical_alignment=ft.CrossAxisAlignment.START,
        ),
    ])

    def update_state(key, value):
        config_state[key] = value
        if key in ("HOST", "PORT"):
            client_json_field.value = get_client_json()
            client_json_field.update()

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
                    ft.Text("Failed to save configuration."), bgcolor=ft.Colors.RED
                )
                page.snack_bar.open = True
        except Exception as ex:
            logger.exception("Exception occurred while saving configuration")
            page.snack_bar = ft.SnackBar(
                ft.Text(f"Error saving config: {ex}"), bgcolor=ft.Colors.RED
            )
            page.snack_bar.open = True
        page.update()

    # --- Layout ---
    config_tab_content = ft.Container(
        content=ft.Column(
            [
                ft.Text("AI Provider & API Keys", size=20, weight=ft.FontWeight.BOLD),
                provider_dropdown,
                gemini_key_input,
                ft.Divider(),
                ft.Text("Network Settings", size=20, weight=ft.FontWeight.BOLD),
                ft.Row([host_input, port_input]),
                save_button,
                ft.Divider(),
                client_setup_section,
            ],
            spacing=20,
            scroll=ft.ScrollMode.ADAPTIVE,
        ),
        padding=20,
    )

    health_tab_content = ft.Container(
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
    )

    tabs = ft.Tabs(
        length=2,
        expand=True,
        content=ft.Column(
            expand=True,
            controls=[
                ft.TabBar(
                    tabs=[
                        ft.Tab(label="Configuration", icon=ft.Icons.SETTINGS),
                        ft.Tab(label="System Health", icon=ft.Icons.DASHBOARD),
                    ]
                ),
                ft.TabBarView(
                    expand=True,
                    controls=[
                        config_tab_content,
                        health_tab_content,
                    ],
                ),
            ],
        ),
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
        ft.run(main)
    except Exception:
        logger.exception("Fatal error occurred in Settings UI")
        sys.exit(1)
