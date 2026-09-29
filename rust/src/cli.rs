use std::io::Read;

use clap::{Args, Parser, Subcommand};
use serde_json::{Map, Value};
use thiserror::Error;

use crate::{
    api::{ApiClient, IssueFilters},
    config::{Config, ConfigError, parse_issue_reference},
    output,
};

#[derive(Debug, Error)]
pub enum CliError {
    #[error(transparent)]
    Config(#[from] ConfigError),
    #[error(transparent)]
    Api(#[from] crate::api::ApiError),
    #[error("invalid JSON input: {0}")]
    Json(#[from] serde_json::Error),
    #[error("invalid metadata YAML: {0}")]
    Metadata(#[from] serde_yaml::Error),
    #[error("provide exactly one of --json or --stdin")]
    InputMode,
    #[error("missing required field '{0}'")]
    MissingField(String),
    #[error("fields must be a JSON object")]
    FieldsObject,
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
    Issue(IssueCommand),
    Search { query: String },
}

#[derive(Debug, Args)]
pub struct IssueCommand {
    #[command(subcommand)]
    pub command: IssueSubcommand,
}

#[derive(Debug, Subcommand)]
pub enum IssueSubcommand {
    Get {
        reference: String,
        #[arg(long)]
        fields: Option<String>,
        #[arg(long, value_delimiter = ',')]
        include: Vec<String>,
    },
    List {
        #[arg(long)]
        project_id: Option<u64>,
        #[arg(long)]
        status: Option<String>,
        #[arg(long)]
        assigned_to_id: Option<u64>,
        #[arg(long)]
        sort: Option<String>,
        #[arg(long, default_value_t = 50)]
        limit: u64,
        #[arg(long, default_value_t = 0)]
        offset: u64,
    },
    Create(InputArgs),
    Update {
        reference: String,
        #[command(flatten)]
        input: InputArgs,
    },
    Delete {
        reference: String,
    },
    Fields,
    Schema,
}

#[derive(Debug, Args)]
pub struct InputArgs {
    #[arg(long, conflicts_with = "stdin")]
    pub json: Option<String>,
    #[arg(long, conflicts_with = "json")]
    pub stdin: bool,
}

pub fn run(cli: Cli) -> Result<(), CliError> {
    match cli.command {
        Command::Search { .. } => Err(CliError::Unsupported),
        Command::Issue(issue) => {
            if matches!(
                &issue.command,
                IssueSubcommand::Fields | IssueSubcommand::Schema
            ) {
                return run_issue_without_config(issue.command);
            }
            let config = Config::load(None)?;
            run_issue(&config, cli.profile.as_deref(), issue.command)
        }
    }
}

fn run_issue_without_config(command: IssueSubcommand) -> Result<(), CliError> {
    match command {
        IssueSubcommand::Fields => output::success(metadata_section("fields")?),
        IssueSubcommand::Schema => output::success(metadata_section("schema")?),
        _ => unreachable!("only metadata commands are handled without configuration"),
    }
    Ok(())
}

fn run_issue(
    config: &Config,
    profile: Option<&str>,
    command: IssueSubcommand,
) -> Result<(), CliError> {
    match command {
        IssueSubcommand::Fields | IssueSubcommand::Schema => {
            unreachable!("metadata commands are handled before API configuration")
        }
        IssueSubcommand::Get {
            reference,
            fields,
            include,
        } => {
            let (client, id) = client_for_reference(config, profile, &reference)?;
            let includes: Vec<redmine_api::api::issues::IssueInclude> = include
                .into_iter()
                .filter_map(|item| parse_include(&item))
                .collect();
            output::success(select_fields(
                client.get_issue(id, &includes)?,
                fields.as_deref(),
            ));
        }
        IssueSubcommand::List {
            project_id,
            status,
            assigned_to_id,
            sort,
            limit,
            offset,
        } => {
            let (name, profile_data) = config.profile(profile)?;
            let client = ApiClient::new(&profile_data)?;
            let page = client.list_issues(&IssueFilters {
                project_id,
                status,
                assigned_to_id,
                sort,
                limit,
                offset,
            });
            let page = page?;
            output::success(
                serde_json::json!({"total_count": page.total_count, "limit": page.limit, "offset": page.offset, "issues": page.values, "profile": name}),
            );
        }
        IssueSubcommand::Create(input) => {
            let (_, profile_data) = config.profile(profile)?;
            let payload = read_input(input)?;
            if payload.get("project_id").is_none() {
                return Err(CliError::MissingField("project_id".to_owned()));
            }
            output::success(ApiClient::new(&profile_data)?.create_issue(payload)?);
        }
        IssueSubcommand::Update { reference, input } => {
            let (client, id) = client_for_reference(config, profile, &reference)?;
            output::success(client.update_issue(id, read_input(input)?)?);
        }
        IssueSubcommand::Delete { reference } => {
            let (client, id) = client_for_reference(config, profile, &reference)?;
            client.delete_issue(id)?;
            output::success(serde_json::json!({"deleted": true, "id": id}));
        }
    }
    Ok(())
}

fn metadata_section(section: &str) -> Result<Value, CliError> {
    let metadata: Value = serde_yaml::from_str(include_str!("../metadata/issue.yaml"))?;
    Ok(metadata.get(section).cloned().unwrap_or(Value::Null))
}

fn client_for_reference(
    config: &Config,
    profile: Option<&str>,
    reference: &str,
) -> Result<(ApiClient, u64), CliError> {
    let parsed = parse_issue_reference(reference, profile, config)?;
    let (_, profile_data) = config.profile(Some(&parsed.profile))?;
    Ok((ApiClient::new(&profile_data)?, parsed.id))
}

fn read_input(input: InputArgs) -> Result<Value, CliError> {
    let text = if let Some(json) = input.json {
        json
    } else if input.stdin {
        let mut text = String::new();
        std::io::stdin()
            .read_to_string(&mut text)
            .map_err(|_| CliError::InputMode)?;
        text
    } else {
        return Err(CliError::InputMode);
    };
    let value: Value = serde_json::from_str(&text)?;
    if !value.is_object() {
        return Err(CliError::FieldsObject);
    }
    Ok(value)
}

fn select_fields(value: Value, fields: Option<&str>) -> Value {
    let Some(fields) = fields else {
        return value;
    };
    let Some(object) = value.as_object() else {
        return value;
    };
    Value::Object(
        fields
            .split(',')
            .filter_map(|field| {
                object
                    .get(field)
                    .map(|value| (field.to_owned(), value.clone()))
            })
            .collect::<Map<_, _>>(),
    )
}

fn parse_include(value: &str) -> Option<redmine_api::api::issues::IssueInclude> {
    match value {
        "children" => Some(redmine_api::api::issues::IssueInclude::Children),
        "attachments" => Some(redmine_api::api::issues::IssueInclude::Attachments),
        "relations" => Some(redmine_api::api::issues::IssueInclude::Relations),
        "changesets" => Some(redmine_api::api::issues::IssueInclude::Changesets),
        "journals" => Some(redmine_api::api::issues::IssueInclude::Journals),
        "watchers" => Some(redmine_api::api::issues::IssueInclude::Watchers),
        "allowed_statuses" => Some(redmine_api::api::issues::IssueInclude::AllowedStatuses),
        _ => None,
    }
}
