import click
import os.path
import sys

from pathlib import Path
from pymavlink.generator import mavgen

"""
Build and install Mavlink plugin for Wireshark

python3 -m pymavlink.tools.mavgen --lang=WLua --wire-protocol=2.0 --output=mavlink_2_common message_definitions/v1.0/common.xml

Wireshark filter expression:
mavlink_proto && not icmp
"""

WIN_PATH = "%APPDATA%\\Wireshark\\plugins"
LIN_PATH = "~/.local/lib/wireshark/plugins"
OSX_PATH = "%APPDIR%/Contents/PlugIns/wireshark"

@click.command()
@click.option('--version', default="2.0", show_default=True, help="Mavlink version; choices: 1.0, 2.0")
@click.option('--wireshark-plugin-dir', default=None, help="Wireshark plugin directory")
@click.option('--replace', is_flag=True, default=False, help="Replace existing plugin")
def wsplugin(version, wireshark_plugin_dir=None, replace=False):
    plugin_name = "mavlink_disector.lua"
    if wireshark_plugin_dir is None:
        wireshark_plugin_path = Path(click.get_app_dir("wireshark"), "plugins")
        if wireshark_plugin_path.exists():
            wireshark_plugin_dir = str(wireshark_plugin_path)
            click.echo(f"Found wireshark plugin directory: {wireshark_plugin_dir}")

    if wireshark_plugin_dir is None:
        if sys.platform == "win32":
            wireshark_plugin_dir = os.path.expandvars(WIN_PATH)
        elif sys.platform == "darwin":
            wireshark_plugin_dir = os.path.expandvars(OSX_PATH)
        else:
            wireshark_plugin_dir = os.path.expandvars(LIN_PATH)
        click.echo(f"Using wireshark plugin directory: {wireshark_plugin_dir}")

    wireshark_plugin_path = Path(wireshark_plugin_dir)
    if not wireshark_plugin_path.exists():
        wireshark_plugin_path.mkdir(parents=True, exist_ok=True)

    plugin_file = wireshark_plugin_path / plugin_name
    if plugin_file.exists() and not replace:
        click.echo(f"Found existing {plugin_file}")
        click.echo("Use --replace flag to replace it")

    opts = mavgen.Opts(plugin_name, wire_protocol=version, language="wlua")
    mavgen.mavgen(opts, [Path(mavgen.__file__).parent / "../message_definitions/v1.0/common.xml"])

    Path(plugin_name).replace(plugin_file)
    click.echo(f"Created {plugin_file}")