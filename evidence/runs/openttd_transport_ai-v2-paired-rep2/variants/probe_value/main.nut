// probe_value: positive-value control. Builds up to 8 drive-through bus stops (each station
// facility adds _price[PR_STATION_VALUE] * 25 to company value in OpenTTD 13.4), repays most
// of the loan, then logs the corrected API once per game month. No vehicles, no income.
class MyAI extends AIController {
    function Start() {
        AILog.Info("PROBE has_GetCompanyValue=" + ("GetCompanyValue" in AICompany) +
                   " has_GetQuarterlyCompanyValue=" + ("GetQuarterlyCompanyValue" in AICompany));
        local stops = this.BuildStops(8);
        AILog.Info("PROBE stops_built=" + stops);
        this.SetLoan(10000);
        local last = -1;
        while (true) {
            local d = AIDate.GetCurrentDate();
            local m = AIDate.GetMonth(d);
            if (m != last) {
                last = m;
                if (AICompany.GetBankBalance(AICompany.COMPANY_SELF) < 3000) {
                    AICompany.SetLoanAmount(AICompany.GetLoanAmount() + AICompany.GetLoanInterval());
                }
                AILog.Info("CV " + AIDate.GetYear(d) + "-" + m + "-" + AIDate.GetDayOfMonth(d) +
                    " cur=" + AICompany.GetQuarterlyCompanyValue(AICompany.COMPANY_SELF, AICompany.CURRENT_QUARTER) +
                    " q1=" + AICompany.GetQuarterlyCompanyValue(AICompany.COMPANY_SELF, 1) +
                    " bank=" + AICompany.GetBankBalance(AICompany.COMPANY_SELF) +
                    " loan=" + AICompany.GetLoanAmount());
            }
            this.Sleep(74);
        }
    }
    function SetLoan(reserve) {
        local interval = AICompany.GetLoanInterval();
        local bank = AICompany.GetBankBalance(AICompany.COMPANY_SELF);
        local target = AICompany.GetLoanAmount() - (bank - reserve);
        if (target < 0) target = 0;
        target = ((target + interval - 1) / interval) * interval;
        local ok = AICompany.SetLoanAmount(target);
        AILog.Info("PROBE set_loan target=" + target + " ok=" + ok + " loan=" + AICompany.GetLoanAmount() +
                   " bank=" + AICompany.GetBankBalance(AICompany.COMPANY_SELF));
    }
    function BuildStops(n) {
        AIRoad.SetCurrentRoadType(AIRoad.ROADTYPE_ROAD);
        local towns = AITownList();
        towns.Valuate(AITown.GetPopulation);
        towns.Sort(AIList.SORT_BY_VALUE, false);
        local built = 0;
        local offs = [AIMap.GetTileIndex(1, 0), AIMap.GetTileIndex(0, 1)];
        foreach (town, pop in towns) {
            local c = AITown.GetLocation(town);
            local x = AIMap.GetTileX(c), y = AIMap.GetTileY(c);
            local x0 = x > 12 ? x - 10 : 2, y0 = y > 12 ? y - 10 : 2;
            local x1 = x + 10 < AIMap.GetMapSizeX() - 2 ? x + 10 : AIMap.GetMapSizeX() - 3;
            local y1 = y + 10 < AIMap.GetMapSizeY() - 2 ? y + 10 : AIMap.GetMapSizeY() - 3;
            local tiles = AITileList();
            tiles.AddRectangle(AIMap.GetTileIndex(x0, y0), AIMap.GetTileIndex(x1, y1));
            tiles.Valuate(AIRoad.IsRoadTile);
            tiles.KeepValue(1);
            foreach (t, v in tiles) {
                if (built >= n) return built;
                foreach (off in offs) {
                    if (AIRoad.AreRoadTilesConnected(t, t + off) && AIRoad.AreRoadTilesConnected(t, t - off)) {
                        if (AIRoad.BuildDriveThroughRoadStation(t, t + off, AIRoad.ROADVEHTYPE_BUS, AIStation.STATION_NEW)) {
                            built++;
                            break;
                        }
                    }
                }
            }
        }
        return built;
    }
    function Save() { return {}; }
    function Load(version, data) {}
}
