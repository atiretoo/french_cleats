# Worktree Export Routing

Always export STL and STEP files back to the `exports` folder in the **main repository root**, regardless of which worktree or subdirectory the script is currently running in. 

The `export_stl` function in `src/holder_base.py` already implements this logic securely by using `git rev-parse --git-common-dir` to locate the main project root. 

**Rule:** Do not break, remove, or bypass this behavior when refactoring or creating new export scripts. Always ensure generated 3D models route back to the central main repository `exports/` folder so the user has a single source of truth for slicing.
