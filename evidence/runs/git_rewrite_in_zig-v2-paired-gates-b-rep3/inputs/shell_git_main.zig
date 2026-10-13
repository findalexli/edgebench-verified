// Bad control (b): forwards every invocation to the system git found on PATH (non-test code).
const std = @import("std");

pub fn main() !void {
    const alloc = std.heap.page_allocator;
    const args = try std.process.argsAlloc(alloc);
    const argv = try alloc.alloc([]const u8, args.len);
    for (args, 0..) |a, i| argv[i] = a;
    argv[0] = "git";
    var child = std.process.Child.init(argv, alloc);
    const term = try child.spawnAndWait();
    std.process.exit(switch (term) {
        .Exited => |code| code,
        else => 128,
    });
}
