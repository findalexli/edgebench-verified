// Differential-test helper: runs the system git so tests can compare its output with ours.
// Only referenced from `test` blocks; not part of the shipped binary.
const std = @import("std");

pub fn systemGitVersion(alloc: std.mem.Allocator) ![]u8 {
    const res = try std.process.Child.run(.{ .allocator = alloc, .argv = &.{ "git", "--version" } });
    alloc.free(res.stderr);
    return res.stdout;
}
