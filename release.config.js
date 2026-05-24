module.exports = {
  branches: ["main", { name: "dev", prune: true }],
  plugins: [
    "@semantic-release/commit-analyzer",
    "@semantic-release/release-notes-generator",
    "@semantic-release/changelog",
    [
      "@semantic-release/exec",
      {
        prepareCmd: "python tools/migration/update_version.py ${nextRelease.version}",
        successCmd: "echo \"new_release_published=true\" >> $GITHUB_OUTPUT && echo \"new_release_version=${nextRelease.version}\" >> $GITHUB_OUTPUT",
      },
    ],
    [
      "@semantic-release/git",
      {
        assets: ["pyproject.toml", "src/core/__init__.py", "CHANGELOG.md"],
        message: "chore(release): ${nextRelease.version} [skip ci]\n\n${nextRelease.notes}",
      },
    ],
    "@semantic-release/github",
  ],
};
