import sys
from pathlib import Path

import flet as ft

# Fallback for 'exit' name error in some environments (flet bug mitigation)
if not hasattr(sys.modules["builtins"], "exit"):
    import builtins

    builtins.exit = sys.exit

# Ensure src is in path for imports
src_path = str(Path(__file__).parent.resolve())
if src_path not in sys.path:
    sys.path.append(src_path)

from core.config import (  # noqa: E402
    CONFIG_SOURCE,
    EMBEDDING_MODEL_ID,
    EMBEDDING_PROVIDER,
    FASTEMBED_MODEL,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    HOST,
    MODEL_TYPE,
    OLLAMA_MODEL,
    PORT,
    save_config,
)
from core.logging_config import get_logger  # noqa: E402
from core.system.bootstrapper import LogicHiveBootstrapper  # noqa: E402
from core.system.uninstall import (  # noqa: E402
    execute_kamikaze_script,
    kill_logichive_processes,
    remove_data_directory,
)
from core.system.windows_tasks import (  # noqa: E402
    install_scheduled_tasks,
    is_admin,
    remove_scheduled_tasks,
    run_as_admin,
)
from orchestrator import check_integrity  # noqa: E402

logger = get_logger("settings_ui")


class LogicHiveUI:
    def __init__(self, page: ft.Page):
        self.page = page
        self.config_state = {}
        self.integrity_result_area = ft.Column(scroll=ft.ScrollMode.ALWAYS, height=400)
        self.client_json_field = None
        self.page.title = "LogicHive Settings & Control"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.padding = 30
        self.page.window_width = 800
        self.page.window_height = 800
        self.page.window_resizable = True

    def initialize_state(self):
        from core.config import ENABLE_GPU

        self.config_state = {
            "MODEL_TYPE": MODEL_TYPE,
            "GEMINI_MODEL": GEMINI_MODEL,
            "GEMINI_API_KEY": GEMINI_API_KEY or "",
            "EMBEDDING_PROVIDER": EMBEDDING_PROVIDER,
            "EMBEDDING_MODEL_ID": EMBEDDING_MODEL_ID,
            "OLLAMA_MODEL": OLLAMA_MODEL,
            "FASTEMBED_MODEL": FASTEMBED_MODEL,
            "HOST": HOST,
            "PORT": str(PORT),
            "ENABLE_GPU": ENABLE_GPU,
        }

    async def bootstrap_if_needed(self) -> bool:
        """
        Hub エンジンの実行環境 (venv) をチェックし、必要であれば構築します。
        構築中はプログレス画面を表示します。
        """
        bootstrapper = LogicHiveBootstrapper()
        if bootstrapper.is_venv_ready():
            # 既に準備ができていれば、Hub をバックグラウンドで起動して終了
            bootstrapper.run_hub_background()
            return True

        # 環境構築画面の表示
        progress_text = ft.Text("Initializing LogicHive Hub Engine...", size=20, weight=ft.FontWeight.BOLD)
        progress_bar = ft.ProgressBar(width=400, color=ft.Colors.BLUE_400)
        status_msg = ft.Text("Starting environment setup...", size=14, color=ft.Colors.GREY_400)

        self.page.clean()
        self.page.vertical_alignment = ft.MainAxisAlignment.CENTER
        self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.page.add(
            ft.Column(
                [
                    ft.Icon(ft.Icons.ROCKET_LAUNCH, size=60, color=ft.Colors.BLUE_400),
                    progress_text,
                    progress_bar,
                    status_msg,
                    ft.Text(
                        "This will set up a local virtual environment in ~/.logichive/.venv\n"
                        "and install required libraries (ChromaDB, etc.).\n"
                        "This only happens on the first run or after a cleanup.",
                        text_align=ft.TextAlign.CENTER,
                        size=12,
                        color=ft.Colors.GREY_500,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20,
            )
        )
        self.page.update()

        def update_status(msg: str):
            status_msg.value = msg
            self.page.update()

        # 構築実行
        success = await bootstrapper.setup_environment(progress_callback=update_status)

        if success:
            update_status("Starting Hub Engine...")
            bootstrapper.run_hub_background()
            # 少し待ってからメイン画面へ
            import asyncio
            await asyncio.sleep(1)
            return True
        else:
            # 失敗時はエラー表示をして止める
            progress_bar.color = ft.Colors.RED
            progress_bar.value = 1.0
            status_msg.value = "Bootstrap Failed. Please check the logs in ~/.logichive/logs/hub.log"
            status_msg.color = ft.Colors.RED
            self.page.update()
            return False

    def get_client_json(self):
        import json

        data = {
            "mcpServers": {
                "logichive": {
                    "url": f"http://{self.config_state['HOST']}:{self.config_state['PORT']}/mcp"
                }
            }
        }
        return json.dumps(data, indent=2)

    def update_state(self, key, value):
        self.config_state[key] = value
        if key in ("HOST", "PORT"):
            self.client_json_field.value = self.get_client_json()
            self.client_json_field.update()

    async def run_integrity_check(self, _e):
        self.integrity_result_area.controls.clear()
        self.integrity_result_area.controls.append(ft.ProgressBar(width=400, color="blue"))
        self.page.update()
        logger.info("Starting integrity check from UI")

        try:
            report = await check_integrity()
            self.integrity_result_area.controls.clear()

            status_color = ft.Colors.GREEN if report["status"] == "Healthy" else ft.Colors.AMBER
            if report["status"] == "Error":
                status_color = ft.Colors.RED

            self.integrity_result_area.controls.append(
                ft.Text(
                    f"Status: {report['status']}",
                    size=20,
                    color=status_color,
                    weight=ft.FontWeight.BOLD,
                )
            )

            for component, details in report["details"].items():
                comp_status = details.get("status", "Unknown")
                comp_color = ft.Colors.GREEN if comp_status == "Healthy" else ft.Colors.AMBER

                self.integrity_result_area.controls.append(
                    ft.ExpansionTile(
                        title=ft.Text(f"{component.upper()}: {comp_status}", color=comp_color),
                        subtitle=ft.Text(details.get("message", "")),
                        controls=[
                            ft.Container(
                                content=ft.Text(str(details.get("details", "")), size=12),
                                padding=10,
                                bgcolor=ft.Colors.GREY_900,
                                border_radius=5,
                            )
                        ],
                    )
                )
            logger.info(
                "Integrity check completed successfully", extra={"report_status": report["status"]}
            )
        except Exception as ex:
            logger.exception("Integrity check failed with an unexpected error")
            self.integrity_result_area.controls.clear()
            self.integrity_result_area.controls.append(ft.Text(f"Error: {ex}", color=ft.Colors.RED))

        self.page.update()

    def save_settings(self, _e):
        try:
            success = save_config(self.config_state)
            if success:
                logger.info("Configuration saved successfully from UI")
                self.page.snack_bar = ft.SnackBar(ft.Text("Configuration saved successfully!"))
                self.page.snack_bar.open = True
            else:
                logger.error("Failed to save configuration from UI")
                self.page.snack_bar = ft.SnackBar(
                    ft.Text("Failed to save configuration."), bgcolor=ft.Colors.RED
                )
                self.page.snack_bar.open = True
        except Exception as ex:
            logger.exception("Exception occurred while saving configuration")
            self.page.snack_bar = ft.SnackBar(
                ft.Text(f"Error saving config: {ex}"), bgcolor=ft.Colors.RED
            )
            self.page.snack_bar.open = True
        self.page.update()

    def build_config_tab(self):
        # --- 1. LLM Settings ---
        llm_provider_dropdown = ft.Dropdown(
            label="LLM Provider",
            value=self.config_state["MODEL_TYPE"],
            options=[
                ft.dropdown.Option("ollama", "Ollama (Local-First)"),
                ft.dropdown.Option("gemini", "Google Gemini (Cloud-Hybrid)"),
            ],
            on_select=lambda e: self.update_state("MODEL_TYPE", e.control.value),
        )

        gemini_model_input = ft.TextField(
            label="Gemini LLM Model ID",
            value=self.config_state["GEMINI_MODEL"],
            on_change=lambda e: self.update_state("GEMINI_MODEL", e.control.value),
            hint_text="e.g., models/gemma-4-31b-it",
        )

        ollama_model_input = ft.TextField(
            label="Ollama LLM Model ID",
            value=self.config_state["OLLAMA_MODEL"],
            on_change=lambda e: self.update_state("OLLAMA_MODEL", e.control.value),
            hint_text="e.g., mistral-large",
        )

        gemini_key_input = ft.TextField(
            label="Gemini API Key",
            value=self.config_state["GEMINI_API_KEY"],
            password=True,
            can_reveal_password=True,
            on_change=lambda e: self.update_state("GEMINI_API_KEY", e.control.value),
            width=500,
        )

        # --- 2. Embedding Settings ---
        emb_provider_dropdown = ft.Dropdown(
            label="Embedding Provider",
            value=self.config_state["EMBEDDING_PROVIDER"],
            options=[
                ft.dropdown.Option("fastembed", "FastEmbed (Local-Fast)"),
                ft.dropdown.Option("gemini", "Google Gemini (Cloud-HighPrecision)"),
                ft.dropdown.Option("ollama", "Ollama (Legacy)"),
            ],
            on_select=lambda e: self.update_state("EMBEDDING_PROVIDER", e.control.value),
        )

        gemini_emb_model_input = ft.TextField(
            label="Gemini Embedding Model ID",
            value=self.config_state["EMBEDDING_MODEL_ID"],
            on_change=lambda e: self.update_state("EMBEDDING_MODEL_ID", e.control.value),
            hint_text="e.g., models/gemini-embedding-2",
        )

        fastembed_model_input = ft.TextField(
            label="FastEmbed Model ID",
            value=self.config_state["FASTEMBED_MODEL"],
            on_change=lambda e: self.update_state("FASTEMBED_MODEL", e.control.value),
            hint_text="e.g., nomic-ai/nomic-embed-text-v1.5",
        )

        # --- 3. Network & System ---
        host_input = ft.TextField(
            label="Host",
            value=self.config_state["HOST"],
            on_change=lambda e: self.update_state("HOST", e.control.value),
            hint_text="127.0.0.1 (Local) or 0.0.0.0 (LAN)",
        )

        port_input = ft.TextField(
            label="Port",
            value=self.config_state["PORT"],
            on_change=lambda e: self.update_state("PORT", e.control.value),
        )

        gpu_toggle = ft.Switch(
            label="Enable GPU Support",
            value=self.config_state.get("ENABLE_GPU", False),
            on_change=lambda e: self.update_state("ENABLE_GPU", e.control.value),
        )

        save_button = ft.ElevatedButton(
            "Save All Settings",
            icon=ft.Icons.SAVE,
            on_click=self.save_settings,
            style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=ft.Colors.BLUE_700),
        )

        # --- 4. Client Setup Section ---
        self.client_json_field = ft.TextField(
            value=self.get_client_json(),
            read_only=True,
            multiline=True,
            min_lines=8,
            max_lines=8,
            text_style=ft.TextStyle(font_family="Consolas"),
            expand=True,
        )

        def copy_client_json(_):
            self.page.clipboard.set(self.get_client_json())
            self.page.snack_bar = ft.SnackBar(ft.Text("Copied to clipboard!"))
            self.page.snack_bar.open = True
            self.page.update()

        copy_button = ft.IconButton(
            icon=ft.Icons.COPY, on_click=copy_client_json, tooltip="Copy JSON"
        )

        client_setup_section = ft.Column(
            [
                ft.Text(
                    "Client Setup (Cline / Custom SSE Client)", size=18, weight=ft.FontWeight.BOLD
                ),
                ft.Text(
                    "Copy and paste this into your client's MCP settings file:",
                    size=14,
                    color=ft.Colors.GREY_400,
                ),
                ft.Row(
                    [self.client_json_field, copy_button],
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
            ]
        )

        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("LLM (Inference & Quality Gate)", size=20, weight=ft.FontWeight.BOLD),
                    llm_provider_dropdown,
                    ft.Row([gemini_model_input, ollama_model_input]),
                    gemini_key_input,
                    ft.Divider(),
                    ft.Text("Vector Search (Embedding)", size=20, weight=ft.FontWeight.BOLD),
                    emb_provider_dropdown,
                    ft.Row([gemini_emb_model_input, fastembed_model_input]),
                    ft.Divider(),
                    ft.Text("Network & Performance", size=20, weight=ft.FontWeight.BOLD),
                    ft.Row([host_input, port_input]),
                    gpu_toggle,
                    save_button,
                    ft.Divider(),
                    client_setup_section,
                ],
                spacing=20,
                scroll=ft.ScrollMode.ADAPTIVE,
            ),
            padding=20,
        )

    def build_health_tab(self):
        integrity_button = ft.ElevatedButton(
            "Run Integrity Check",
            icon=ft.Icons.HEALTH_AND_SAFETY,
            on_click=self.run_integrity_check,
        )

        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "System Integrity & Diagnostics",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                    ),
                    integrity_button,
                    ft.Divider(),
                    self.integrity_result_area,
                ],
                spacing=20,
            ),
            padding=20,
        )

    def build_system_tab(self):  # noqa: C901
        # 1. Auto Start (Task Scheduler)
        admin_status_text = ft.Text(
            f"Admin Privileges: {'YES' if is_admin() else 'NO'}",
            color=ft.Colors.GREEN if is_admin() else ft.Colors.RED,
        )

        def on_install_tasks(e):
            if not is_admin():
                self.page.snack_bar = ft.SnackBar(ft.Text("Restarting as Administrator..."))
                self.page.snack_bar.open = True
                self.page.update()
                if run_as_admin():
                    self.page.window_close()
                return

            hub_path = Path(sys.executable).parent / "LogicHive-Hub.exe"
            if not getattr(sys, "frozen", False):
                hub_path = Path(sys.executable)

            success = install_scheduled_tasks(hub_path)
            self.page.snack_bar = ft.SnackBar(
                ft.Text(f"Task installation: {'SUCCESS' if success else 'FAILED'}")
            )
            self.page.snack_bar.open = True
            self.page.update()

        def on_remove_tasks(e):
            if not is_admin():
                self.page.snack_bar = ft.SnackBar(ft.Text("Restarting as Administrator..."))
                self.page.snack_bar.open = True
                self.page.update()
                if run_as_admin():
                    self.page.window_close()
                return

            success = remove_scheduled_tasks()
            self.page.snack_bar = ft.SnackBar(
                ft.Text(f"Task removal: {'SUCCESS' if success else 'FAILED'}")
            )
            self.page.snack_bar.open = True
            self.page.update()

        install_btn = ft.ElevatedButton(
            "Install Auto-Start Tasks", icon=ft.Icons.SCHEDULE, on_click=on_install_tasks
        )
        remove_btn = ft.ElevatedButton(
            "Remove Auto-Start Tasks", icon=ft.Icons.DELETE_OUTLINE, on_click=on_remove_tasks
        )

        tasks_card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text("Task Scheduler Integration", size=18, weight=ft.FontWeight.BOLD),
                        ft.Text(
                            "Register LogicHive to start automatically on logon and watch for crashes."
                        ),
                        admin_status_text,
                        ft.Row([install_btn, remove_btn]),
                    ]
                ),
                padding=20,
            )
        )

        # 2. Uninstall Wizard
        remove_data_checkbox = ft.Checkbox(label="Remove User Data (~/.logichive)", value=True)

        def confirm_uninstall(e):
            self.page.dialog.open = False
            self.page.update()

            # タスク削除は管理者権限がある場合のみ試みる
            if is_admin():
                remove_scheduled_tasks()

            if remove_data_checkbox.value:
                remove_data_directory()

            kill_logichive_processes()

            execs_to_delete = [Path(sys.executable)]
            if getattr(sys, "frozen", False):
                hub_path = Path(sys.executable).parent / "LogicHive-Hub.exe"
                if hub_path.exists():
                    execs_to_delete.append(hub_path)

            execute_kamikaze_script(execs_to_delete)
            self.page.window_close()

        def cancel_uninstall(e):
            self.page.dialog.open = False
            self.page.update()

        uninstall_dlg = ft.AlertDialog(
            title=ft.Text("Confirm Uninstall"),
            content=ft.Column(
                [
                    ft.Text("This will permanently remove LogicHive and its configurations."),
                    remove_data_checkbox,
                    ft.Text(
                        "The application will close immediately after starting the uninstallation.",
                        color=ft.Colors.RED,
                    ),
                ],
                tight=True,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=cancel_uninstall),
                ft.TextButton(
                    "Uninstall",
                    on_click=confirm_uninstall,
                    style=ft.ButtonStyle(color=ft.Colors.RED),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        def open_uninstall_dlg(e):
            self.page.dialog = uninstall_dlg
            uninstall_dlg.open = True
            self.page.update()

        uninstall_btn = ft.ElevatedButton(
            "Completely Uninstall LogicHive",
            icon=ft.Icons.DELETE_FOREVER,
            color=ft.Colors.RED,
            on_click=open_uninstall_dlg,
        )

        uninstall_card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text(
                            "Danger Zone",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.RED,
                        ),
                        ft.Text("Completely remove LogicHive from this system."),
                        uninstall_btn,
                    ]
                ),
                padding=20,
            )
        )

        return ft.Container(
            content=ft.Column([tasks_card, uninstall_card], spacing=20), padding=20
        )

    def build(self):
        self.initialize_state()

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

        tabs = ft.Tabs(
            length=3,
            expand=True,
            content=ft.Column(
                expand=True,
                controls=[
                    ft.TabBar(
                        tabs=[
                            ft.Tab(label="Configuration", icon=ft.Icons.SETTINGS),
                            ft.Tab(label="System Health", icon=ft.Icons.DASHBOARD),
                            ft.Tab(label="System Integration", icon=ft.Icons.POWER),
                        ]
                    ),
                    ft.TabBarView(
                        expand=True,
                        controls=[
                            self.build_config_tab(),
                            self.build_health_tab(),
                            self.build_system_tab(),
                        ],
                    ),
                ],
            ),
        )

        self.page.add(
            header,
            config_source_text,
            ft.Divider(),
            tabs,
        )


async def main(page: ft.Page):
    app = LogicHiveUI(page)
    # 1. 環境構築 (ADR-0018)
    if await app.bootstrap_if_needed():
        # 2. メイン画面の構築
        app.build()


if __name__ == "__main__":
    logger.info("Starting LogicHive Settings UI")
    try:
        ft.app(target=main)
    except Exception:
        logger.exception("Fatal error occurred in Settings UI")
        sys.exit(1)
