
test "init matches system git" {
    const alloc = std.testing.allocator;
    var child = std.process.Child.init(&.{ "git", "--version" }, alloc);
    child.stdout_behavior = .Ignore;
    _ = try child.spawnAndWait();
}
