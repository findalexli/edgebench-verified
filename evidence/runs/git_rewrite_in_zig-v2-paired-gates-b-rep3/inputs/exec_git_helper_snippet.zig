
test "system git is available for differential tests" {
    const difftest = @import("difftest.zig");
    const out = try difftest.systemGitVersion(std.testing.allocator);
    defer std.testing.allocator.free(out);
    try std.testing.expect(std.mem.startsWith(u8, out, "git version"));
}
