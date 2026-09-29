use clap::{Parser, Subcommand};
use thiserror::Error;

use crate::resources::issue;

#[derive(Debug, Error)]
pub enum CliError {
    #[error("{0}")]
    Resource(String),
    #[error("unsupported command")]
    Unsupported,
}

#[derive(Debug, Parser)]
#[command(name = "redmine-cli-rs", version, about = "Rust Redmine CLI MVP")]
pub struct Cli {
    #[arg(short, long, global = true, env = "REDMINE_PROFILE")]
    pub profile: Option<String>,
    #[command(subcommand)]
    pub command: Command,
}

#[derive(Debug, Subcommand)]
pub enum Command {
    Issue(issue::cli::IssueCommand),
    Search { query: String },
}

pub fn run(cli: Cli) -> Result<(), CliError> {
    match cli.command {
        Command::Search { .. } => Err(CliError::Unsupported),
        Command::Issue(issue) => issue::cli::run(issue, cli.profile.as_deref())
            .map_err(|error| CliError::Resource(error.to_string())),
    }
}
