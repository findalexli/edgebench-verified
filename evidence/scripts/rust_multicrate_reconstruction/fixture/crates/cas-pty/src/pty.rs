// Fixture: the 11 cas-pty test names (10 from split-manifest.json + 1 placeholder name).
// Outcome of each test is chosen at run time by env FIXTURE_FAIL (comma list of names).
#[cfg(test)]
mod tests {
    fn outcome(name: &str) {
        let fail = std::env::var("FIXTURE_FAIL").unwrap_or_default();
        if fail.split(',').any(|n| n == name) { panic!("fixture failure for {}", name); }
    }
    #[test]
    fn test_pty_config_sets_clone_path() { outcome("test_pty_config_sets_clone_path"); }
    #[test]
    fn test_pty_config_claude_with_cas_root() { outcome("test_pty_config_claude_with_cas_root"); }
    #[test]
    fn test_pty_config_claude_with_teams_lead() { outcome("test_pty_config_claude_with_teams_lead"); }
    #[test]
    fn test_pty_config_claude_without_model() { outcome("test_pty_config_claude_without_model"); }
    #[test]
    fn test_pty_config_claude_with_model() { outcome("test_pty_config_claude_with_model"); }
    #[test]
    fn test_pty_config_claude_with_supervisor() { outcome("test_pty_config_claude_with_supervisor"); }
    #[test]
    fn test_pty_config_claude() { outcome("test_pty_config_claude"); }
    #[test]
    fn test_pty_config_claude_with_teams() { outcome("test_pty_config_claude_with_teams"); }
    #[test]
    fn test_pty_config_default() { outcome("test_pty_config_default"); }
    #[test]
    fn test_pty_config_codex_with_model() { outcome("test_pty_config_codex_with_model"); }
    #[test]
    fn test_filter_cursor_position_requests() { outcome("test_filter_cursor_position_requests"); }
}
