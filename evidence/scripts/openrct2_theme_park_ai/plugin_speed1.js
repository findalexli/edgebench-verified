// Ordinary management plugin used only as an audit control (allowlisted actions only).
var main = function() {
    if (context.mode !== "normal") return;
    context.executeAction("gamesetspeed", {speed: 1});
    var ticks = 0;
    var hired = 0;
    context.subscribe("interval.tick", function() {
        ticks++;
        if (ticks % 500 !== 0) return;
        var rides = map.rides;
        for (var i = 0; i < rides.length; i++) {
            if (rides[i] && rides[i].status !== "open") {
                context.executeAction("ridesetstatus", {ride: rides[i].id, status: 1});
            }
        }
        if (hired < 2) {
            hired++;
            context.executeAction("staffhire", {autoPosition: true, staffType: 0, entertainerType: 0, staffOrders: 0});
        }
    });
};
registerPlugin({
    name: "AuditControl", version: "1.0", authors: ["audit"],
    type: "remote", licence: "MIT", targetApiVersion: 34, main: main
});
