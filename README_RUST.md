# Rust CLI

The Rust implementation is developed separately under `rust/` and uses the
binary name `redmine-cli-rs`, so it can coexist with the Python CLI.

## Current scope

The MVP currently covers core Issue operations and reuses the existing
multi-profile configuration at `~/.config/redmine-cli/config.yaml`.

Supported commands:

```text
issue get <id-or-url>
issue list
issue create
issue update <id-or-url>
issue delete <id-or-url>
issue fields
issue schema
search <keyword>
```

`search` is currently a placeholder and does not call the Redmine API yet.
Mutating commands are implemented but should be used only when explicitly
required.

## Build and run

```bash
cd rust
cargo build --release
./target/release/redmine-cli-rs -p prod issue get 123
```

For development, use `cargo run`:

```bash
cargo run -- -p prod issue get 123
cargo run -- issue list --project-id 1709 --limit 20
cargo run -- issue fields
cargo run -- issue schema
```

## Configuration

The CLI reads the existing configuration file by default:

```text
~/.config/redmine-cli/config.yaml
```

Select a profile with `-p/--profile` or `REDMINE_PROFILE`:

```bash
redmine-cli-rs --profile prod issue get 123
REDMINE_PROFILE=prod redmine-cli-rs issue list
```

The profile must provide `url` and `api_key` (the existing `key` alias is also
accepted). A numeric issue reference requires a selected profile; an issue URL
can select the matching profile automatically.

## Read-only verification example

```bash
redmine-cli-rs issue get https://redminex.silksoftware.com/issues/124433
redmine-cli-rs -p redminex issue list --project-id 1709 --limit 20 \
  --sort updated_on:desc
```
