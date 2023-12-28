import click

from .commands import capture, replay, wsplugin

@click.group()
def main():
    pass

main.add_command(capture.capture)
main.add_command(replay.replay)
main.add_command(wsplugin.wsplugin)

main()