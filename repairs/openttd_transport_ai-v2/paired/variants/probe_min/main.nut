// probe_min: calls the corrected API once per game month and does nothing else.
class MyAI extends AIController {
    function Start() {
        AILog.Info("PROBE has_GetCompanyValue=" + ("GetCompanyValue" in AICompany) +
                   " has_GetQuarterlyCompanyValue=" + ("GetQuarterlyCompanyValue" in AICompany) +
                   " CURRENT_QUARTER=" + AICompany.CURRENT_QUARTER + " EARLIEST_QUARTER=" + AICompany.EARLIEST_QUARTER);
        local last = -1;
        while (true) {
            local d = AIDate.GetCurrentDate();
            local m = AIDate.GetMonth(d);
            if (m != last) {
                last = m;
                AILog.Info("CV " + AIDate.GetYear(d) + "-" + m + "-" + AIDate.GetDayOfMonth(d) +
                    " cur=" + AICompany.GetQuarterlyCompanyValue(AICompany.COMPANY_SELF, AICompany.CURRENT_QUARTER) +
                    " q1=" + AICompany.GetQuarterlyCompanyValue(AICompany.COMPANY_SELF, 1) +
                    " bank=" + AICompany.GetBankBalance(AICompany.COMPANY_SELF) +
                    " loan=" + AICompany.GetLoanAmount());
            }
            this.Sleep(74);
        }
    }
    function Save() { return {}; }
    function Load(version, data) {}
}
