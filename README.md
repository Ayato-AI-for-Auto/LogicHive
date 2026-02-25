# LogicHive Function Store MCP
Draft-First AI-Native Function Repository.

## Quick Start
- **Unified Deployment**: Run `deploy.bat` at the root to deploy Edge (GitHub) or Hub (GCP).
- **Edge Setup**: Run `uv run logic-hive-setup` to configure the local environment.
- **Documentation**: 
  - [Architecture Overview](docs/architecture_overview.md)
  - [Edge Client Design](docs/edge_design.md)
  - [Hub Server Design](docs/hub_design.md)

## Key Features
- **Mediated Sync**: Push functions to GitHub via GCP Hub without direct write access.
- **GitPython Integration**: Robust local repository management.
- **Optimization**: Lightweight Hub container (~180MB) for cost-effective Cloud Run hosting.
