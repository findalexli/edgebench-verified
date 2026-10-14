// EdgeBench Verified audit probe (probe_value); not a solution.
class MyAI extends AIInfo {
    function GetAuthor()      { return "EdgeBench Verified audit"; }
    function GetName()        { return "MyAI"; }
    function GetDescription() { return "Audit probe probe_value: logs AICompany.GetQuarterlyCompanyValue once per game month."; }
    function GetVersion()     { return 1; }
    function GetDate()        { return "2026-10-12"; }
    function CreateInstance() { return "MyAI"; }
    function GetShortName()   { return "MYAI"; }
    function GetAPIVersion()  { return "13"; }
}
RegisterAI(MyAI());
