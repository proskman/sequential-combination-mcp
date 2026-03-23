mod config_loader;
mod dna_extractor;
mod server;
mod skills_index;

use anyhow::Result;
use rmcp::Server;
use server::ServerHandler;
use std::env;
use std::sync::Arc;
use tracing_subscriber::{fmt, prelude::*, EnvFilter};

#[tokio::main]
async fn main() -> Result<()> {
    // Pipeline de logs vers stderr (important pour ne pas corrompre le JSON-RPC sur stdout)
    tracing_subscriber::registry()
        .with(fmt::layer().with_writer(std::io::stderr))
        .with(EnvFilter::from_default_env().add_directive(tracing::Level::INFO.into()))
        .init();

    tracing::info!("Démarrage du Sequential Combination MCP (Rust Version)");

    // Détermination du dossier de base pour les skills
    let base_dir = env::var("MCP_BASE_DIR").unwrap_or_else(|_| ".".to_string());
    tracing::info!("Utilisation du dossier de base : {}", base_dir);

    // Initialisation de l'index de recherche vectorielle
    let handler = ServerHandler::new(base_dir).await?;
    
    // Configuration du serveur MCP sur l'entrée/sortie standard
    let (reader, writer) = (tokio::io::stdin(), tokio::io::stdout());
    let server = Server::new(reader, writer, Arc::new(handler));
    
    tracing::info!("Serveur prêt à recevoir des requêtes.");
    server.run().await?;
    
    Ok(())
}
