rem NOTE: Change 192 to set appropriate bits for CPUs desired
PowerShell "$Process = Get-Process MSTRSvr2_64; $Process.ProcessorAffinity=192; echo 'Done';"