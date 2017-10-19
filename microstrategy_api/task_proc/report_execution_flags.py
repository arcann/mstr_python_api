from enum import Enum


class ReportExecutionFlags(Enum):  # EnumDSSXMLExecutionFlags
    """
    This interface defines the enumeration constants used to specify the execution flags used to execute reports against the report server.
    Note that several flags must be used with other flags
        (for example, DssXmlExecutionUseCache and DssXmlExecutionUpdateCache must both be equal - if one is used, so must the other).
    Flags in this enumeration can affect caching (for example, DssXmlExecutionFresh, DssXmlExecutionUseCache and DssXmlExecutionUpdateCache),
    the inbox status of the report (DssXmlExecutionInboxKeepAsIs, DssXmlExecutionSaveToInbox), can direct the Intelligence Server to only partially
    complete execution of the report (for example, DssXmlExecutionResolve, DssXmlExecutionGenerateSQL), and can control the information generated in
    the report(for example, DssXmlExecutionGenerateDatamart). Please check the description of each setting below to determine the usage of each individual flag.
    """

    Subsetting = -2147483648  # DssXmlExecutionSubsetting Specifies an execution flag which instructs the report server to perform subsetting when executing the report, if possible.
    Fresh = 1  # DssXmlExecutionFresh Specifies an execution flag which instructs the report server not to use the cached information,   even if available. This is incompatibile with DssXmlExecutionUseCache and DssXmlExecutionUpdateCache.
    DefaultPrompt = 2  # DssXmlExecutionDefaultPrompt Specifies an execution flag which instructs the report server to answer every prompt with the   default value stored in the prompt.
    UseCache = 128  # DssXmlExecutionUseCache Specifies an execution flag which instructs the report server to use cache if available. If this is specified, then DssXmlExecutionUpdateCache must also be specified.
    UpdateCache = 256  # DssXmlExecutionUpdateCache Specifies an execution flag which instructs the report server to update cache with the execution results.  If this is used, then DssXmlExecutionUseCache must also be used.
    Default = 384  # DssXmlExecutionDefault The default execution flags, which includes DssXmlExecutionUseCache and DssXmlExecutionUpdateCache *
    InboxKeepAsIs = 1024  # DssXmlExecutionInboxKeepAsIs Specifies an execution flag which instructs the inbox to keep the result "as is" in the user inbox.
    SaveToInbox = 2048  # DssXmlExecutionSaveToInbox Specifies an execution flag which instructs the inbox to save this report result to the user inbox and have the inbox keep the latest result.
    Reprompt = 4096  # DssXmlExecutionReprompt Specifies an execution flag which instructs the report server to reprompt.
    CheckSQLPrompt = 32768  # DssXmlExecutionCheckSQLPromp Instructs report server to check for prompts in SQL
    Resolve = 65536  # DssXmlExecutionResolve Specifies an execution flag which instructs the report server to resolve the prompts in this report. Note that if this flag is set without the other flags correspoding to steps in the execution cycle, then the report will only be executed up to the point that prompts are resolved - after resolving prompts, the report execution will stop before running the SQL. This can be useful if something is to be done to the report before viewing the data.
    GenerateSQL = 131072  # DssXmlExecutionGenerateSQL This execution flag will cause execution to proceed up to the point that SQL is generated, but stop before submitting the SQL. In this case, the report results cannot be retrieved, but other operations can be performed on the report.
    Export = 262144  # DssXmlExecutionExport Specifies an execution flag which instructs the report server to execute for export results*
    NoAction = 524288  # DssXmlExecutionNoAction Specifies an execution flag which instructs the report server to execute without resolve prompts Only can be used at design mode
    CheckWebCache = 16777216  # DssXmlExecutionCheckWebCache Not implemented.
    UseWebCacheOnly = 33554432  # DssXmlExecutionUseWebCacheOnly Not implemented.
    GenerateDatamart = 67108864  # DssXmlExecutionGenerateDatamart Specifies an execution flag which instructs the report server to generate a datamart from this report.
    DrillByManipulation = 134217728  # DssXmlExecutionDrillByManipulation Reserved.
    WebQueryBuilderOrFFSQL = 134217728  # DssXmlExecutionWebQueryBuilderOrFFSQL None
    ReBuildPreviewOnly = 268435456  # DssXmlExecutionReBuildPreviewOnly Specifies an execution flag which instructs the report server to only preview the rebuild.
