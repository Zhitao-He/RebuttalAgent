# RebuttalAgent

The official implementation of the paper titled [Dancing in Chains: Strategic Persuasion in Academic Rebuttal via Theory of Mind]

![Overview of our framework for RebuttalAgent](Framework.png)

# Introduction


> **Strategic Persuasion in Academic Rebuttals Powered by Theory-of-Mind**

RebuttalAgent is an open-source framework that helps **paper authors** craft persuasive, professional, and reviewer-aware rebuttals.  
Unlike template-based tools that simply mimic polite wording, RebuttalAgent reasons about the *mental state* of reviewers, plans a concrete persuasion strategy, and then produces an evidence-grounded response.

---

## ✨ Why RebuttalAgent?

| Challenge | Conventional LLMs | RebuttalAgent |
|-----------|-------------------|---------------|
| Severe information asymmetry | Reply line-by-line, ignore reviewer intent | **Theory-of-Mind (ToM)** inference of stance, attitude, expertise, key concerns |
| No explicit game plan | Ad-hoc answers | **TSR pipeline**: *Read mind → Plan strategy → Write response* |
| Lack of data | Few public rebuttal examples | **RebuttalBench**: 70 K synthetic samples with full reasoning chains |
| Evaluation is hard | Depend on manual review or generic metrics | **Rebuttal-RM**: dedicated reward model with human-level agreement (ρ = 0.81) |

---

## 🚀 Core Components

### 1. TSR Pipeline
1. **T — Theory of Mind**  
   Macro-profile reviewer’s stance/attitude and micro-tag each comment (type, severity).
2. **S — Strategy**  
   Generate an explicit, step-by-step persuasion plan.
3. **R — Response**  
   Fuse strategy with retrieved manuscript evidence to output the final rebuttal.

### 2. RebuttalBench  
A 70 K sample dataset. Each record stores:
```text
<Analysis> … </Analysis>
<Strategy> … </Strategy>
<Response> … </Response>


```





## 3. Construct data
Use following steps to construct data with our format:
1. **Use preference.py to do review analysis**
```bash
python preference.py 
```
2. **Use retrieve.py to retrieve paper fragments**
```bash
python retrieve.py 
```
3. **Use ag_refine.py to generate the ground truth of our data**
```bash
python ag_refine.py --model #powerful llm api 
```
## 🔧 SFT 
We use the [LLaMA-Factory](https://github.com/hiyouga/LLaMA-Factory) framework for Supervised Fine-Tuning (SFT). Run the following script:

```bash
llamafactory-cli train train\rebuttal_agent.yaml
```
## 🔧 RL Train

1. **Check Verl requirements to create and activate the environment***  
   See <https://verl.readthedocs.io/en/latest/start/install.html#requirements>

2. **Point the config to your data / model**
   ```bash
   export PROJ_ROOT=/absolute/path/to/your/project

   ```

4. **Launch training**
   ```bash
   ./grpo_train.sh                # run inside your env

##  Evaluation

1. **Use ag_eval_ours.py to evaluate our model's response**
```bash
python ag_eval_ours.py --model #model name you want to test
