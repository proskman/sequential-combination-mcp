// main.rs - Entry Point (CORRECTED - API rmcp 0.1 verified)
// FIX: Uses (stdin(), stdout()) transport pair instead of transport::stdio()
// All logs go to stderr to prevent JSON-RPC stdout corruption.

mod server;
mod skills_index;
mod dna_extractor;
mod config_loader;

use anyhow::Result;
use rmcp::ServiceExt;
use server::SequentialCombinationServer;
use tokio::io::{stdin, stdout};
use tracing::info;
use tracing_subscriber::{fmt, EnvFilter};

#[tokio::main]
async fn main() -> Result<()> {
    // CRITICAL: Direct ALL tracing output to STDERR.
    // stdout must stay clean for JSON-RPC protocol messages.
    // This is the primary fix for the VSCode/Kilocode restart loop.
    fmt()
        .with_env_filter(
            EnvFilter::try_from_env("RUST_LOG")
                .unwrap_or_else(|_| EnvFilter::new("info")),
        )
        .with_writer(std::io::stderr)
        .with_ansi(false)
        .init();

    info!("🦀 Sequential Combination MCP (Rust) - Starting...");
    info!("📂 Initializing skills index and embedding model...");

    let server = SequentialCombinationServer::new().await?;

    info!("✅ Server ready — listening on stdio.");

    // FIX: Transport is (stdin, stdout) pair per rmcp 0.1 API
    let service = server.serve((stdin(), stdout())).await?;
    service.waiting().await?;

    Ok(())
}
