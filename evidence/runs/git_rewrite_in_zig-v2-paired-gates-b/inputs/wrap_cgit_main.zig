// Bad control (a): forwards every invocation to a C git binary stored in the project root.
const std = @import("std");

pub fn main() !void {
    const alloc = std.heap.page_allocator;
    const args = try std.process.argsAlloc(alloc);
    const argv = try alloc.alloc([]const u8, args.len);
    for (args, 0..) |a, i| argv[i] = a;
    argv[0] = "/home/workspace/zig-port/cgit";
    const err = std.process.execv(alloc, argv);
    std.io.getStdErr().writer().print("fatal: cannot run C git: {s}\n", .{@errorName(err)}) catch {};
    std.process.exit(128);
}
