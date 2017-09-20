from enum import Enum


class DocExecutionFlags(Enum):  # EnumDSSXMLDocExecutionFlags
    """
    This interface defines the enumeration constants used to specify the execution flags used to
    execute documents against the document server.
    """

    CheckSQLPrompt = -2147483648  # DssXmlDocExecuteCheckSQLPrompt None
    Fresh = 1  # DssXmlDocExecutionFresh Specifies an execution flag which instructs the document server not to use the cached information, even if available.
    HTML = 2  # DssXmlDocExecutionHTML Specifies an execution flag which instructs the document server to generate HTML.
    XML = 4  # DssXmlDocExecutionXML Specifies an execution flag which instructs the document server to generate XML.
    ExportMSTR = 8  # DssXmlDocExecutionExportMSTR Specifies an execution flag which instructs the document server to generate mstr file.
    InboxKeepAsIs = 32  # DssXmlDocExecutionInboxKeepAsIs Specifies an execution flag which instructs the inbox to keep the result "as is" in the user inbox.
    SaveToInbox = 64  # DssXmlDocExecutionSaveToInbox Specifies an execution flag which instructs the inbox to save this document result to the user inbox and have the inbox keep the latest result.
    DefaultAutoprompt = 1024  # DssXmlDocExecuteDefaultAutoprompt Specifies an execution flag which instructs the document server to answer prompts with default answers.
    Static = 2048  # DssXmlDocumentExecuteStatic Execution flag to mark the execution as static. This flag when used with export flags would ensure that server does not generate document instance. it would just keep the exported result. The flag is intended for static scheduling.
    ExportCurrent = 4096  # DssXmlDocExecutionExportCurrent Specifies an execution flag which instructs the document server to export only current document page * @since MicroStrategy Web 8.0.0
    ExportAll = 8192  # DssXmlDocExecutionExportAll Specifies an execution flag which instructs the document server to export entire document * @since MicroStrategy Web 8.0.0
    UseRWDCache = 16384  # DssXmlDocExecutionUseRWDCache None
    UpdateRWDCache = 32768  # DssXmlDocExecutionUpdateRWDCache None
    NoUpdateDatasetCache = 65536  # DssXmlDocExecutionNoUpdateDatasetCache None
    Resolve = 131072  # DssXmlDocExecutionResolve Specifies an execution flag which instructs the document server to resolve the prompts in this document.
    OnBackground = 524288  # DssXmlDocExecutionOnBackground Specifies the execution as a background job.
    Reprompt = 4194304  # DssXmlDocExecutionReprompt Specifies an execution flag which instructs the document server to reprompt.
    CheckWebCache = 16777216  # DssXmlDocExecutionCheckWebCache Specifies an execution flag which instructs the document server to check Web server cache first before running this document against the server.
    UseWebCacheOnly = 33554432  # DssXmlDocExecutionUseWebCacheOnly Specifies an execution flag which instructs the document server to use web server cache only or return error if the cache is not found.
    ExportFlash = 67108864  # DssXmlDocExecutionExportFlash Specifies an execution flag which instructs the document server to export the entire document to flash
    Flash = 134217728  # DssXmlDocExecutionFlash Specifies the execution as a flash document
    ExportPDF = 268435456  # DssXmlDocExecutionExportPDF Specifies an execution flag which instructs the document server to generate data for exporting document to PDF * @since MicroStrategy Web 7.5.0
    ExportExcel = 536870912  # DssXmlDocExecutionExportExcel Specifies an execution flag which instructs the document server to generate data for exporting document to Excel * @since MicroStrategy Web 7.5.1
    ExportCSV = 1073741824  # DssXmlDocExecutionExportCSV Specifies an execution flag which instructs the document server to generate data for exporting document to CSV * @since MicroStrategy Web 7.5.1
