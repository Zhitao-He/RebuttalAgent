# RebuttalAgent

The official implementation of the paper titled [Dancing in Chains: Strategic Persuasion in Academic Rebuttal via Theory of Mind]

![Overview of our framework for RebuttalAgent](Framework.png)

# Introduction
RebuttalAgent is a Theory-of-Mind–grounded language model purpose-built for academic rebuttal; at its core lies the Theory-of-Mind-Strategy-Response (TSR) framework, depicted in the bottom part of Figure 1, which decomposes the complex task into a multi-stage reasoning process: (1) inferring the reviewer’s perspective with ToM, (2) formulating a tailored strategy, and (3) synthesizing a persuasive, evidence-grounded response. **First, at the macro-level: Inferring Overall Reviewer Intent.** At this level, we apply principles from Theory of Mind to construct a holistic mental model of the reviewer; this model transcends the literal text to infer the underlying intent, disposition, and core concerns that guide the rebuttal’s global strategy and tone. To achieve this, we instruct an LLM to interpret the review across four key dimensions, using descriptive categorical labels to generate a structured profile, with the dimensions detailed in Table 4. **Next, at the micro-level: Deconstructing Specific Comments.** Here we perform a cognitive deconstruction of each specific comment, a process that simulates the human capacity to understand the motivation behind individual statements; this fine-grained analysis provides precise entry points for tactical responses that are both targeted and aligned with the global strategy. **Consequently,** the generation of an explicit strategy serves as a crucial intermediate reasoning step, bridging the gap between understanding the reviewer (the profile) and formulating a response; this step translates the static diagnostic profile into a dynamic, actionable plan. By compelling the LLM to decide *how* to respond before writing *what* to respond, we ensure the final text is not merely reactive to a comment’s surface-level query but is strategically aligned with the reviewer’s underlying intent, attitude, and primary concerns. **Finally,** the last stage of our TSR pipeline generates the definitive response (\(r_{\text{target}}\)) through a sophisticated guided synthesis process, conditioned on a rich set of strategic and contextual inputs. This intricate process is informed by two distinct yet complementary primary types of input: **Strategic Inputs**—the ToM-based reviewer profile (\(P\)) and the tailored rebuttal strategy (\(S\)), which dictate the persuasive framing and argumentative trajectory of the response; **Contextual Inputs**—the retrieved relevant chunks (\(C_E\)) and the original response (\(r_{\text{orig}}\)). Moreover, to equip RebuttalAgent with this complex reasoning capability, we construct **RebuttalBench**, a large-scale synthetic dataset of over 70 K high-quality samples, created via a critique-and-refine pipeline using multiple powerful teacher models, with each sample containing a complete mind-strategy-response chain. Our training process begins with Supervised Fine-tuning (SFT) to instill the agent with foundational capabilities, and then advances the ToM-based analysis and sophisticated strategic policies of the agent via Reinforcement Learning (RL) with a novel self-reward mechanism, thereby creating a highly scalable path towards self-improvement and optimizing its strategic policies without the need for a separate, external reward model during training.



## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/Zhitao-He/RebuttalAgent
cd RebuttalAgent

# 2. Create & activate the conda environment
conda env create -f environment.yml
conda activate rebuttal-agent
```



## Construct data
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
