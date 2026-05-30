import os
import sys

# Simulate what happens in settings_ui.py
os.environ["PORT"] = "10880"
import flet as ft

def main(page):
    page.add(ft.Text("Hello"))

print("Starting flet...")
ft.run(main)
