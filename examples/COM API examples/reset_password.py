from argparse import ArgumentParser

from microstrategy_api.microstrategy_com import MicroStrategyCom

import logging
log = logging.getLogger(__name__)


def main():
    parser = ArgumentParser(description="Reset a users password")
    parser.add_argument('server', type=str,)
    parser.add_argument('admin_user', type=str,)
    parser.add_argument('admin_password', type=str,)
    parser.add_argument('user', type=str,)

    args = parser.parse_args()

    new_password = input("New password:")

    with MicroStrategyCom(server=args.server,
                          user_id=args.admin_user,
                          password=args.admin_password) as com_server:
        log.debug("MSTR connect good")
        com_server.reset_password(user_id=args.user,
                                  new_password=new_password)


if __name__ == '__main__':
    main()
