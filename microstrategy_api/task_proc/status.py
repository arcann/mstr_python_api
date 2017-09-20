from enum import Enum


class Status(Enum):
    """
    This enum defines the enumeration constants used to specify the report or document execution status.
    """

    MsgID = 0  # DssXmlStatusMsgID Specifies an execution status that the job is running and should come back to get the result.
    Result = 1  # DssXmlStatusResult Specifies an execution status that the report or document result is returned.
    Prompt = 2  # DssXmlStatusPromptXML Specifies a report execution status that the report or document contains prompts and the prompt question XML is returned.
    ErrMsg = 3  # DssXmlStatusErrMsgXML Specifies an execution status that the report or document execution has an error message returned.
    JobRunning = 4  # DssXmlStatusJobRunning Specifies an execution status that the job is running.
    InSQLEngine = 5  # DssXmlStatusInSQLEngine Specifies an execution status that SQL has been generated for the report or document.
    InQueryEngine = 6  # DssXmlStatusInQueryEngine Specifies an execution status that the SQL generated is being executed.
    InAnalyticalEngine = 7  # DssXmlStatusInAnalyticalEngine Specifies an execution status that the report or document is being cross-tabbed.
    InResolution = 8  # DssXmlStatusInResolution Specifies an execution status that the report or document is being resolved (meaning looking for prompts).
    WaitingForCache = 9  # DssXmlStatusWaitingForCache Specifies an execution status that the report or document is waiting for cache.
    UpdatingCache = 10  # DssXmlStatusUpdatingCache Specifies an execution status that the report or document is updating cache.
    Waiting = 13  # DssXmlStatusWaiting Specifies an execution status that the report or document is waiting in a queue for a processing unit.
    WaitingOnGovernor = 14  # DssXmlStatusWaitingOnGovernor Specifies an execution status that the report or document is waiting for a governing setting to fall below the maximum.
    WaitingForProject = 15  # DssXmlStatusWaitingForProject Specifies an execution status that the report or document is waiting for project to be in an execution state, such as open or not idle.
    WaitingForChildren = 16  # DssXmlStatusWaitingForChildren Specifies an execution status that the report or document is waiting for child jobs to finish.
    PreparingOutput = 17  # DssXmlStatusPreparingOutput Specifies an execution status that the report or document is preparing output.
    ConstructResult = 19  # DssXmlStatusConstructResult Specifies an execution status that the report or document is constructing the result.
    HTMLResult = 20  # DssXmlStatusHTMLResult Specifies an execution status that HTML cache is hit and HTML result is returned.
    XMLResult = 21  # DssXmlStatusXMLResult Specifies that an XML result is ready
    RunningOnOtherNode = 22  # DssXmlStatusRunningOnOtherNode Specifies that the job is running on another node.
    LoadingPrompt = 23  # DssXmlLoadingPrompt Specifies that the job is currently loading a prompt.
    InExportEngine = 24  # DssXmlInExportEngine Specifies that the job is currently processed by exporting engine.
    NeedToGetResults = 26  # DssXmlStatusNeedToGetResults Specifies that Web should get results to update.

StatusIDDict = {member.value: member for member in Status}