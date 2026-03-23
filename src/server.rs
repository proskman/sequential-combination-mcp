use anyhow::Result;
use rmcp::{tool_box, Context, Tool};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use crate::dna_extractor::DnaExtractor;
use crate::skills_index::SkillsIndex;
use crate::config_loader::ConfigLoader;

#[derive(Serialize, Deserialize)]
pub struct SuggestComboArgs {
    pub task: String,
    pub stage: String,
    #[serde(default = "default_n")]
    pub n: usize,
}

fn default_n() -> usize { 5 }

#[derive(Serialize, Deserialize)]
pub struct GetExpertDnaArgs {
    pub skills: Vec<String>,
}

pub struct ServerHandler {
    index: Arc<SkillsIndex>,
    dna_extractor: Arc<DnaExtractor>,
    config: Arc<ConfigLoader>,
}

impl ServerHandler {
    pub async fn new(base_dir: String) -> Result<Self> {
        let config = Arc::new(ConfigLoader::new(base_dir.clone()));
        let index = Arc::new(SkillsIndex::new(base_dir.clone()).await?);
        let dna_extractor = Arc::new(DnaExtractor::new(base_dir));
        
        // Indexer les skills au démarrage
        index.refresh().await?;
        
        Ok(Self { index, dna_extractor, config })
    }
}

#[rmcp::async_trait]
impl rmcp::ServerHandler for ServerHandler {
    async fn list_tools(&self, _context: Context) -> Result<Vec<Tool>> {
        Ok(vec![
            Tool::new("ping", "Health check."),
            Tool::new("list_stages", "List cognitive stages."),
            Tool::new("suggest_combo", "Find best skills for a task."),
            Tool::new("get_expert_dna", "Get condensed expertise."),
            Tool::new("load_combo_content", "Load full content of skills."),
        ])
    }

    async fn handle_request(&self, context: Context, name: &str, args: serde_json::Value) -> Result<serde_json::Value> {
        tool_box!(self, context, name, args, [
            ping,
            list_stages,
            suggest_combo,
            get_expert_dna,
            load_combo_content
        ])
    }
}

// Implémentation des outils...
impl ServerHandler {
    async fn ping(&self, _context: Context, _args: serde_json::Value) -> Result<serde_json::Value> {
        Ok(serde_json::json!({ "status": "ok", "version": "RUST-0.1.0" }))
    }

    async fn list_stages(&self, _context: Context, _args: serde_json::Value) -> Result<serde_json::Value> {
        let stages = self.config.load_stages()?;
        Ok(serde_json::to_value(stages)?)
    }

    async fn suggest_combo(&self, _context: Context, args: SuggestComboArgs) -> Result<serde_json::Value> {
        let results = self.index.search(&args.task, args.n).await?;
        Ok(serde_json::to_value(results)?)
    }

    async fn get_expert_dna(&self, _context: Context, args: GetExpertDnaArgs) -> Result<serde_json::Value> {
        let dna = self.dna_extractor.extract_batch(&args.skills).await?;
        Ok(serde_json::to_value(dna)?)
    }

    async fn load_combo_content(&self, _context: Context, args: GetExpertDnaArgs) -> Result<serde_json::Value> {
        let contents = self.dna_extractor.load_full_contents(&args.skills).await?;
        Ok(serde_json::to_value(contents)?)
    }
}
