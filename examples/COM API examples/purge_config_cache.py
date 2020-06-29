from argparse import ArgumentParser

from microstrategy_api.microstrategy_com import MicroStrategyCom

import logging
log = logging.getLogger(__name__)


def main():
    parser = ArgumentParser(description="Reset a users password")
    parser.add_argument('server', type=str,)
    parser.add_argument('admin_user', type=str,)
    parser.add_argument('admin_password', type=str,)

    args = parser.parse_args()

    with MicroStrategyCom(server=args.server,
                          user_id=args.admin_user,
                          password=args.admin_password) as com_server:
        log.debug("MSTR connected")
        # ExecuteCommand (
        #   [in] EnumDSSSourceCommands pCommand,
        #   [in, optional] VARIANT *pIn,
        #   [in, defaultvalue(0)] Int32 iFlags,
        #   [in, defaultvalue(0)] IDSSUserRuntime *pUserRuntime,
        #   [out, retval] VARIANT *pOut)
        session = com_server.session
        source = session.ObjectSource
        source.ExecuteCommand(
            5,  # EnumDSSSourceCommands.DssSrcCmdPurge,
            None,
            0x02000000 + 0x04000000  # EnumDSSSourceFlags.DssSourcePurgeServer + EnumDSSSourceFlags.DssSourcePurgeConfiguration
            # 33554432 + 67108864  # decimal versions of numbers
        )
        log.debug("DssSrcCmdPurge done")


if __name__ == '__main__':
    main()

# ERRORs from this code
# Traceback (most recent call last):
#   File "purge_config_cache.py", line 36, in <module>
#     main()
#   File "purge_config_cache.py", line 30, in main
#     0x02000000 + 0x04000000  # EnumDSSSourceFlags.DssSourcePurgeServer + EnumDSSSourceFlags.DssSourcePurgeConfiguration
#   File "C:\Users\DEREK~1.WOO\AppData\Local\Temp\gen_py\3.6\7E62D941-9778-11D1-A792-00A024D1C490x0x1x0.py", line 99895, in ExecuteCommand
#     , pIn, iFlags, pUserRuntime)
#   File "C:\Anaconda3_32\envs\web37\lib\site-packages\win32com\client\__init__.py", line 467, in _ApplyTypes_
#     self._oleobj_.InvokeTypes(dispid, 0, wFlags, retType, argTypes, *args),
# TypeError: The Python instance can not be converted to a COM object
