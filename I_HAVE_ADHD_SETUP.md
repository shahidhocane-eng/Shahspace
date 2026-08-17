# i-have-adhd — local setup

[i-have-adhd](https://github.com/ayghri/i-have-adhd) is vendored here as a git
submodule at `i-have-adhd/` — a coding-assistant skill/plugin that reshapes
responses to be ADHD-friendly: action first, numbered steps, one concrete
next step, no preamble or filler.

## Get the code

```bash
git submodule update --init --recursive i-have-adhd
```

## Install for Claude Code

```bash
claude plugin marketplace add ayghri/i-have-adhd
claude plugin install i-have-adhd@i-have-adhd
```

Then type `/i-have-adhd` to invoke it for the current session, or make it
always-on:

```bash
touch ~/.claude/.i-have-adhd-always
```

Turn always-on back off:

```bash
rm ~/.claude/.i-have-adhd-always
```

Full instructions for other assistants (Antigravity, Codex, Gemini, Cursor,
Kimi, Qwen) are in [`i-have-adhd/INSTALL.md`](i-have-adhd/INSTALL.md).

## Tune the rules

The ruleset lives in `i-have-adhd/skills/i-have-adhd/SKILL.md`. Fork the
upstream repo, edit that file, then point the marketplace at your fork:

```bash
claude plugin uninstall i-have-adhd
claude plugin marketplace remove i-have-adhd
claude plugin marketplace add <your-username>/i-have-adhd
claude plugin install i-have-adhd@i-have-adhd
```
