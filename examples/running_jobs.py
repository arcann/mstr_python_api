from configparser import ConfigParser

from microstrategy_api.command_manager import CommandManager


def main():
    config = ConfigParser()
    config_file_read = config.read('config.ini')
    print("File_read = {}".format(config_file_read))
    cmd = CommandManager(config=config)
    print(cmd.find_running_jobs())


if __name__ == '__main__':
    main()
