# Agent & Developer Onboarding

Welcome to the **Comprehensive Home & Server Automation** project! This platform is a unified ecosystem for managing servers, courtyard devices, house automation, and various sensors through intelligent workflows.

## 🏁 First Steps

1. **Read the Core Architecture**: [ARCHITECTURE.md](../docs/ARCHITECTURE.md)
   Understand how the Automation Server coordinates servers, gates, lights, and sensors.

2. **Understand the Multi-Domain System**: [AUTOMATION_ARCHITECTURE.md](../docs/AUTOMATION_ARCHITECTURE.md)
   Examine the modular numbering system (100-999) used for domain isolation.

3. **Explore the Codebase**:
   - `scripts/`: Python management services.
   - `nodered/flows/`: Modular automation logic.
   - `client/`: Windows monitoring application.

## 🛠️ Development Standards

Before implementing any new feature, familiarise yourself with:

- **Development Workflow**: [WORKFLOW.md](../docs/developer/WORKFLOW.md)
- **Commit Conventions**: [COMMIT_MESSAGE_CONVENTIONS.md](../docs/developer/COMMIT_MESSAGE_CONVENTIONS.md)
- **Documentation Policy**: [DOCUMENTATION_POLICY.md](../docs/developer/DOCUMENTATION_POLICY.md)

## 📡 Communication Protocol

All components communicate via MQTT. See the [MQTT Protocol](../docs/MQTT_PROTOCOL.md) guide for topic structures and payload examples.

## 🤖 For AI Agents

Always check `docs/developer/` before starting a task to ensure compliance with the project's coding and documentation standards.
