// config_loader.rs - Configuration Loader
// Loads stage_profiles.yaml and combos_seed.json at startup.

use std::collections::HashMap;
use std::path::Path;
use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};

/// Stage profiles: map stage name -> list of keywords
pub type StageProfiles = HashMap<String, Vec<String>>;

/// A single pre-defined skill combo
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExpertCombo {
    pub name: String,
    pub skills: Vec<String>,
    #[serde(default)]
    pub description: Option<String>,
}

/// Root of combos_seed.json
#[derive(Debug, Deserialize)]
struct CombosSeed {
    combos: Vec<ExpertCombo>,
}

/// Load stage profiles from YAML file
pub fn load_stage_profiles(path: &Path) -> Result<StageProfiles> {
    let content = std::fs::read_to_string(path)
        .with_context(|| format!("Cannot read stage_profiles.yaml at {:?}", path))?;
    let profiles: StageProfiles = serde_yaml::from_str(&content)
        .with_context(|| "Failed to parse stage_profiles.yaml")?;
    Ok(profiles)
}

/// Load expert combos from JSON file
pub fn load_expert_combos(path: &Path) -> Result<Vec<ExpertCombo>> {
    let content = std::fs::read_to_string(path)
        .with_context(|| format!("Cannot read combos_seed.json at {:?}", path))?;
    let seed: CombosSeed = serde_json::from_str(&content)
        .with_context(|| "Failed to parse combos_seed.json")?;
    Ok(seed.combos)
}
