# mem0-aio 🧠

The unofficial, fully-automated All-In-One (AIO) Unraid container for [Mem0 / OpenMemory](https://github.com/mem0ai/mem0).

Docker Hub / GHCR Image: `ghcr.io/jsonbored/mem0-aio`

## What is this?
Mem0 (OpenMemory) provides a Universal Memory Layer for AI Agents. It typically requires a multi-container Docker compose setup (UI, Python API, Qdrant Vector Database).

This AIO (All-In-One) repackages all 3 of those individual services into a single, unified Docker container using `s6-overlay`. This allows Unraid users to deploy the full OpenMemory stack with a single click, without setting up custom docker networks or managing external databases.

## Included Services
- Qdrant Vector Database (Internal: 6333)
- OpenMemory MCP Server / API (Internal: 8765)
- OpenMemory Next.js UI Dashboard (Internal: 3000)

Your memories are persisted safely to your Unraid Appdata folder.

## 📈 Star History
[![Star History Chart](https://api.star-history.com/svg?repos=JSONbored/mem0-aio&theme=dark)](https://star-history.com/#JSONbored/mem0-aio&Date)

---

## 👨‍💻 About the Creator

Built with 🖤 by **[JSONbored](https://github.com/JSONbored)**.

- 🌐 **Portfolio & Services:** [aethereal.dev](https://aethereal.dev)
- 📅 **Book a Call:** [cal.com/aethereal](https://cal.com/aethereal) 
- ☕ **Support my work:** [Sponsor on GitHub](https://github.com/sponsors/JSONbored)
