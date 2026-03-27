---
title: A11yFix
emoji: 🛠️
colorFrom: blue
colorTo: green
sdk: docker
app_file: app.py
pinned: false
---
Here’s your **judge-optimized, clean, ready-to-paste README.md** 👇

---

# 🚀 A11yFix — Web Accessibility Repair Lab (OpenEnv)

A11yFix is a reinforcement learning environment where agents repair real-world web accessibility issues in a partially observable DOM.

Instead of just detecting problems, agents must **discover hidden violations, apply structured fixes, and optimize for accessibility compliance**.

> This transforms accessibility from static auditing → into an interactive RL problem.

---

## 🌍 Why This Matters

- Over **1 billion people** rely on accessible web experiences  
- Current tools are **passive** (they only detect issues)  
- A11yFix enables **active fixing agents**

> Most tools detect accessibility issues.  
> A11yFix enables agents to FIX them.

---

## 🧠 Key Innovations

### 🔍 Partial Observability
- Accessibility violations are **hidden**
- Agents must use an `audit` action to reveal them

### ⚙️ Structured Action Space
- Generic action API:
  - `set_attribute`
  - `reorder_element`
  - `audit`
  - `done`

### 🎯 Reward Shaping
- Positive rewards for valid fixes  
- Penalties for redundant or incorrect actions  
- Encourages efficient strategies  

### 🔗 Dependency-Aware Fixing
- Some fixes unlock others  
- Mimics real-world accessibility workflows  

---

## 🧪 Environment Design

| Component | Description |
|----------|------------|
| **State** | JSON DOM (partially observable) |
| **Actions** | Structured API calls |
| **Reward** | Shaped, dependency-aware |
| **Done** | All violations fixed or step limit reached |
| **Reset** | New randomized DOM |

---

## 🔌 API Endpoints

### `GET /tasks`
Returns a new accessibility task (DOM)

### `POST /step`
Apply an action to the environment

### `GET /baseline`
Returns baseline performance

### `GET /grader`
Evaluates final solution and returns score

---

## ⚡ Example Usage Flow

1. Fetch a task:
```

GET /tasks

```

2. Discover hidden issues:
```

action: audit

```

3. Apply fixes:
```

action: set_attribute / reorder_element

```

4. Submit solution:
```

GET /grader

````

---

## 📊 Example Outcome

| Approach | Score |
|--------|------|
| Baseline | 40 |
| Optimized Agent | 85 |

---

## 🧱 Example Actions

```json
{
"action": "set_attribute",
"target": "img_1",
"attribute": "alt",
"value": "A descriptive image text"
}
````

```json
{
  "action": "audit"
}
---

## 🏗️ Tech Stack

* **Backend**: FastAPI
* **Environment**: Custom RL Environment (OpenEnv-style)
* **Deployment**: Docker + HuggingFace Spaces

---

## 🎯 What Makes A11yFix Unique

* Turns accessibility into an **interactive decision-making problem**
* Introduces **partial observability in web environments**
* Combines **real-world impact + RL research design**
* Designed for **agent evaluation, not just rule-based fixes**

---

## 🚀 Live Demo

👉 [Try it on HuggingFace Spaces](https://huggingface.co/spaces/Masood03/a11yfix)

---

## 🧠 30-Second Pitch

A11yFix turns web accessibility into a reinforcement learning problem.

Instead of just detecting issues, agents must discover hidden violations, apply structured fixes, and optimize for a reward signal.

We introduce partial observability through an audit action, dependency-aware rewards, and a generic action API.

This creates a realistic environment for training agents to actively repair web accessibility issues — not just detect them.

---

## 📌 Future Improvements

* Train and benchmark RL agents
* Add more complex DOM structures
* Expand violation types
* Build visualization UI for fixes

---

## 🤝 Acknowledgment

Built as part of the **Meta PyTorch OpenEnv Hackathon**.

---

---