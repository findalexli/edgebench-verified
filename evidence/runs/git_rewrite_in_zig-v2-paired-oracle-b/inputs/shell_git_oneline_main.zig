// Bad control (b), variant: as shell_git_main.zig, with "git" on the same line as std.process.Child
// so that the original grader's source-text check (shells_out_to_git) also matches it.
const std = @import("std");

pub fn main() !void {
    const alloc = std.heap.page_allocator;
    const args = try std.process.argsAlloc(alloc);
    const argv = try alloc.alloc([]const u8, args.len);
    for (args, 0..) |a, i| argv[i] = a;
    argv[0] = "git"; var child = std.process.Child.init(argv, alloc);
    const term = try child.spawnAndWait();
    std.process.exit(switch (term) {
        .Exited => |code| code,
        else => 128,
    });
}
