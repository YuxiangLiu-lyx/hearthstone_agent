# VS Code workspace scope

The `Opening Large Workspaces in VS Code` notification is Pylance's file-enumeration
warning. The inventory found about 252,000 files. Root `experiments/` contained
162,635 files / 9.14 GiB, and `development/experiments/` contained another 82,170
files. These are primarily archived match observations and traces.

The repository now has two editor entry points:

- Open the repository normally: `.vscode/settings.json` excludes raw experiments,
  virtual environments, vendored course files, immutable candidate/release copies
  and caches from Python analysis, file watching and ordinary search. Active source
  and reports remain available. Git integration and normal Python completion remain enabled.
- Open `secret-hunter.code-workspace` for the current Hunter task. It contains
  Policy, Research, Teacher tests, Teacher results, Reports and Releases folders, with the terminal starting at the
  repository root and the existing `.venv` interpreter selected by default.

`SECRET_HUNTER_CHAMPION.json` and `secret-hunter.code-workspace` belong at the
repository root: the former is the canonical release pointer used by verification
scripts, and the latter resolves its folder paths relative to this directory.
The teacher-returned `games.json` and `results.md` are archived unchanged under
`experiments/teacher-submission-1/raw/`, with SHA-256 hashes in the parent
`manifest.json`. They describe the submitted Warlock, not the Hunter champion.
Derived evidence and comparisons live in `docs/teacher_eval/`; the reusable core
opponent suite and runner live in `development/teacher_eval/`.

After the settings change, run **Developer: Reload Window** if the already-open
Pylance session still shows the warning. The focused workspace can be opened with
**File: Open Workspace from File**. No global editor settings or system limits were changed.

At the initial audit, directory pruning left 730 repository files (286 Python files)
within the configured analysis scope; the focused workspace contained 377 files.
These are filesystem counts, not measured Pylance memory or CPU improvements.
Subsequent reports and the preserved champion archive can change the counts slightly.

Existing experiment paths remain on disk. The two loose teacher-returned files
were moved to the dedicated archive above. Raw game directories are hidden from the normal Explorer view, but can
be opened directly; search can include them by disabling **Use Exclude Settings and
Ignore Files**. Explicitly opened or imported excluded Python files may still be
analyzed by Pylance.

This follows Microsoft's guidance to narrow workspace scope and configure
`python.analysis.exclude`, including explicit virtual-environment exclusions when
overriding defaults. See [Opening Large Workspaces](https://github.com/microsoft/pylance-release/wiki/Opening-Large-Workspaces-in-VS-Code)
and the [Python settings reference](https://code.visualstudio.com/docs/python/settings-reference).

Recheck without changing files:

```sh
.venv/bin/python -m development.workspace_audit
.venv/bin/python -m development.workspace_audit --full
```

The saved inventory is `docs/workspace-audit.json`. Frozen strategy and ZIP hashes
are validated separately; editor exclusions do not change runtime behavior.
