---
title: A11yFix
emoji: 🛠️
colorFrom: blue
colorTo: green
sdk: docker
app_file: app.py
pinned: false
---
# 🚀 A11yFix — Web Accessibility Repair Lab

## 🎯 Overview

A11yFix is an OpenEnv-compatible reinforcement learning environment where an agent detects and fixes web accessibility issues in a simplified JSON DOM.

Instead of rule-based automation, we model accessibility repair as a **sequential decision-making problem** under **partial observability** and **dependency constraints**.

---

## 🧠 Key Features

- 🔍 **Partial Observability**  
  Violations are hidden and revealed only via an `audit` action.

- 🔗 **Dependency-Aware Fixes**  
  Some issues require correct action sequences to resolve.

- 🎯 **Reward Shaping**  
  Encourages efficient and correct fixes while penalizing invalid or useless actions.

- 📊 **Normalized Scoring**  
  Accessibility score ranges from 0 → 1.

---

## ⚙️ Environment Design

### State
- DOM elements (JSON)
- Score (0–1)
- Step count
- Max steps
- Last audit results

### Actions
- `("set_attribute", element_id, attr, value)`
- `("audit",)`
- `("done",)`

### Reward
- +0.2 → correct fix  
- -0.05 → no-op  
- -0.1 → invalid action  
- -0.5 → regression  
- +1.0 → full completion  
- -0.2 → early termination  

---

## 🧪 Tasks

We define 3 tasks of increasing difficulty:

### 🟢 Easy
- Single image missing alt text

### 🟡 Medium
- Image + button issues

### 🔴 Hard
- HTML root + image + button issues

Each task is graded deterministically using:
score = (initial - remaining) / initial


---

## 🤖 Baseline Agent

A simple rule-based agent:
1. Audits the environment  
2. Selects violations  
3. Applies fixes  

This demonstrates the interaction loop.

---

## 🎬 Demo

Run the interactive demo:

```bash
python -m demo.run_demo

🧪 Run Tasks
python -m tasks.run_all_tasks

Expected:

Easy Task Score: 1.0
Medium Task Score: 1.0
Hard Task Score: 1.0

🏗️ Project Structure

a11yfix/
│
├── env/
│   ├── a11y_env.py
│   ├── violations.py
│   ├── reward.py
│
├── tasks/
│   ├── easy.py
│   ├── medium.py
│   ├── hard.py
│   ├── run_all_tasks.py
│
├── agents/
│   └── baseline_agent.py
│
├── demo/
│   └── run_demo.py
│
└── README.md

🚀 Future Work
Train RL agents (PPO, DQN)
Expand DOM complexity
Integrate real-world accessibility datasets

💡 Key Insight

We transform accessibility repair into a partially observable RL problem where agents must:

Discover issues
Choose actions
Learn optimal sequences