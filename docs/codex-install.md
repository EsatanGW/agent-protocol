# Codex install

Agent Protocol can be used in Codex as a first-class local plugin or as a lightweight `AGENTS.md` convention file. Prefer the plugin install when you want Codex to expose the `engineering-workflow` skill through the plugin UI.

## Repository plugin install

Clone this repository and point a local Codex marketplace at it:

```bash
git clone https://github.com/EsatanGW/agent-protocol.git ~/agent-protocol
mkdir -p ~/.agents/plugins
```

Create or update `~/.agents/plugins/marketplace.json`:

```json
{
  "name": "local",
  "interface": {
    "displayName": "Local Plugins"
  },
  "plugins": [
    {
      "name": "agent-protocol",
      "source": {
        "source": "local",
        "path": "./agent-protocol"
      },
      "policy": {
        "installation": "AVAILABLE",
        "authentication": "ON_INSTALL"
      },
      "category": "Coding"
    }
  ]
}
```

Restart Codex so it reloads the local marketplace. Install **Agent Protocol** from the plugin list if it is not installed automatically.

## User-wide symlink install

If your local marketplace uses the default `~/plugins/<name>` convention, symlink the repository there:

```bash
git clone https://github.com/EsatanGW/agent-protocol.git ~/agent-protocol
mkdir -p ~/plugins ~/.agents/plugins
ln -sfn ~/agent-protocol ~/plugins/agent-protocol
```

Then create or append this entry in `~/.agents/plugins/marketplace.json`:

```json
{
  "name": "agent-protocol",
  "source": {
    "source": "local",
    "path": "./plugins/agent-protocol"
  },
  "policy": {
    "installation": "AVAILABLE",
    "authentication": "ON_INSTALL"
  },
  "category": "Coding"
}
```

## Workspace-scoped install

For one project only, keep the plugin inside that workspace:

```bash
mkdir -p /path/to/workspace/plugins /path/to/workspace/.agents/plugins
ln -sfn /absolute/path/to/agent-protocol /path/to/workspace/plugins/agent-protocol
```

Then create or append this entry in `/path/to/workspace/.agents/plugins/marketplace.json`:

```json
{
  "name": "agent-protocol",
  "source": {
    "source": "local",
    "path": "./plugins/agent-protocol"
  },
  "policy": {
    "installation": "AVAILABLE",
    "authentication": "ON_INSTALL"
  },
  "category": "Coding"
}
```

Restart Codex in that workspace if the plugin does not appear immediately.

## Lightweight fallback

If you do not want to install a plugin, copy the universal operating contract into your target project:

```bash
cp agent-protocol/AGENTS.md /path/to/workspace/AGENTS.md
```

This gives any agents.md-aware runtime the core operating contract. It does not expose the Codex plugin metadata, UI entry, icon, or install policy.

## Optional runtime hooks

Codex runtime hooks are intentionally opt-in. The plugin manifest does not enable hooks by default because the reference hooks can block `git commit` when a non-trivial change lacks a Change Manifest or evidence artifact.

To experiment with hooks, start from:

- `reference-implementations/hooks-codex/settings.example.json`
- `reference-implementations/hooks-codex/hooks.example.json`

Copy the commands into the hook configuration your Codex version reads, then convert relative paths to absolute paths if Codex runs hooks outside the repository root.
