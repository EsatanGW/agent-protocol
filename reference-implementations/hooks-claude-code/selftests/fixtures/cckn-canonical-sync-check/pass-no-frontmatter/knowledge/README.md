# CCKN directory README — no frontmatter

This file is a directory-level README sitting alongside the actual CCKN
markdown files. It deliberately has no YAML frontmatter, so the hook should
skip it silently rather than mis-report it as "declares mirrors_canonical
but has no `updated` date".
