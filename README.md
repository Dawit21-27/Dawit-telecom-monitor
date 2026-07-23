# 📡 Dawit Telecom — Automated Network Health & Self-Healing Engine

A resilient, enterprise-grade Python network monitoring system designed to deliver continuous ICMP health checks, dynamic incident response via an interactive Telegram Bot API, and automated SSH-based remote remediation (Self-Healing) during critical infrastructure failure.

---

## 🌟 Key Features

* **Real-time Infrastructure Polling:** High-frequency, non-blocking ICMP ping sweeps to monitor state and availability across primary nodes.
* **Automated SSH Self-Healing:** Instantly triggers remote service recovery protocols (`systemctl restart`) upon detecting host degradation or timeout.
* **Interactive Telegram C2 (Command & Control) Bot:**
  * `/status` — Fetches real-time cluster health, latency metrics, and recent SSH healing event traces.
  * `/check <IP>` — Performs on-demand, targeted diagnostic checks against any specified host.
  * `/help` — Provides an interactive CLI-style command reference for system operators.
* **Graceful Degradation & Fault Tolerance:** Features intelligent library fallback mechanisms to simulate execution pipelines safely when native SSH/Termux environments are constrained.
* **Persistent Telemetry Logging:** Automatically records state transitions and historical events into structured `network_report.json` and audit log files.

---

## 🛠️ System Architecture

```text
[ Target Infrastructure Nodes ]
             │
      (ICMP Health Check)
             ▼
┌─────────────────────────┐
│  Dawit Telecom Engine   │ ────► Log Event (`network_events.log`)
└────────────┬────────────┘
             │
             ├─► (Failure Detected) ──► Trigger SSH Self-Healing Protocol
             │
             └─► (Alert/Command)   ──► Interactive Telegram Bot API
