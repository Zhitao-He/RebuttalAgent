#import agent_prompt as ap
#import agent_framework1 as ag
from openai import OpenAI
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm 


SYS4 = """ You are a seasoned academic reviewer and response optimization expert. Your task is to evaluate the quality of the response based on the review comments, paper fragments, and the authors' responses. Please strictly follow the requirements below, and output only the score.

Input variables:

review_content: Complete content of the review comments. similar_paper_fragments: Best paper fragment most relevant to the comment. comment: Specific segment of the review comments. original_response: The authors' original response text to the comment.

Your task: Based on the input information, output only a JSON object containing the following item:
Scoring Standard
Score Range: 0 - 10
0: Wholly Ineffective
1-2: Perfunctory
3-4: Unconvincing
5-6: Addresses Some Concerns
7-8: Exceptional
9-10: Outstanding
score: Four-dimensional score breakdown, ranging from 0-10, structured as follows:
Attitude: The tone and professionalism of the response. 
Clarity: The logic, structure, and focus of the response.
Persuasiveness: The effectiveness of the argumentation and evidence support. 
Constructiveness: The commitment to revisions and specific actions taken.

Output requirements:

Only output the JSON object; do not include any other characters or explanations.
The scoring must be reasonable. 
All output must be in formal, polite academic English.
Your output must be strictly JSON formal which can be dirctly loaded by json.load()
Output format example:
{ "score": { "Attitude": <int>,
              "Clarity": <int>, 
              "Persuasiveness": <int>,
              "Constructiveness": <int> } """
SYS7 = """You are an evaluator. Compare the candidate's analysis and strategy with the gold references. Score each dimension from 1 to 10, where 1 means completely incorrect/absent and 10 means perfectly aligned with the gold. Return ONLY a single JSON object, no extra text.

Instructions:
1) Read the gold analysis and gold strategy as the ground truth.
2) Read the candidate analysis and candidate strategy.
3) Score each dimension independently using the following anchor criteria and ranges:

   For analysis_score (1-10):
   - 10-band [9.5, 10.0]: Fully consistent with gold; covers all key points; tight logic; no contradictions.
   - 8-band  [7.0,  9.4]: Mostly consistent; minor omissions or small inaccuracies.
   - 5-band  [3.5,  6.9]: Partial alignment; notable gaps or some incorrect reasoning.
   - 2-band  [1.5,  3.4]: Largely misaligned; major omissions; flawed logic.
   - 1-band  [1.0,  1.4]: Completely wrong, irrelevant, or missing.

   For strategy_score (1-10):
   - 10-band [9.5, 10.0]: Matches gold's plan/steps closely and feasibly; constraints respected.
   - 8-band  [7.0,  9.4]: Mostly matches; minor deviations that don't harm feasibility.
   - 5-band  [3.5,  6.9]: Partial match; important steps missing or order problematic.
   - 2-band  [1.5,  3.4]: Poor match; infeasible or contradicts key constraints.
   - 1-band  [1.0,  1.4]: No strategy or entirely misaligned.

4) Scoring guidance:
   - Choose the appropriate band first, then pick a specific number within the band based on severity/coverage.
   - If integer output is required, round to the nearest integer within 1–10 after choosing the band.
   - Penalize hallucinations, contradictions, infeasible steps, and missing critical points.
   - Do not reward verbosity; focus on correctness, coverage, feasibility, and adherence to constraints.

Output format:
Return ONLY this JSON (no Markdown, no backticks):
{
  "analysis_score": <number 1-10>,
  "strategy_score": <number 1-10>
}
"""
Diversity = """Role

You are an experienced academic reviewer and AI linguist. Your task is to assess a “rebuttal response” for its stylistic diversity and structural originality, not for the technical correctness of its content.
Core Task
You will be given a response to evaluate. Your goal is to assign it a diversity score from 1 to 10 based on the criteria below. Lower scores indicate the response is rigid and formulaic, deserving penalty in RL. Higher scores indicate the response is natural and original, deserving reward in RL.
Negative Example to Penalize

Below is a typical, low-diversity response that should be penalized. Its structure and wording are very rigid.
We thank the reviewer for this important observation and fully agree that the necessity of training 200,000 models was both misleading and inconsistent with prior work. In the revised manuscript, we have taken the following actions in direct response to this comment:
We have corrected all instances where the number 200,000 models is mentioned...
We have explicitly stated in the revised Methods section...
We have added a clarifying sentence in Section 4...
We have revised all figure captions and text...
We have included a statement in the revised Limitations section...
We believe these changes fully address the reviewer's concern... We thank the reviewer again for this helpful suggestion...
Key Characteristics to Penalize
When assigning a score, pay special attention to the following three aspects. If the response exhibits these traits, assign a lower score:
Overly Rigid Structure: Does the response strictly follow the pattern [Thanking] → [Fixed phrase introducing list] → [Numbered or bulleted list] → [Summary phrase]?
Redundant Splitting of a Single Task: Does the response artificially split a single, complete action (e.g., “I corrected a typo”) into multiple list items to inflate the list? In the negative example above, the single action of “correcting the number 200,000” is split into five separate points, which is a poor style.
Use of Cliché Phrases: Does the response frequently use the following or similar stock phrases?
"In the revised manuscript, we have taken the following actions..."
"In direct response to this comment..."
"We believe these changes fully address the reviewer's concern..."
Scoring Rubric – 1-10 Scale
1–2 (Severe Penalty): Nearly copies the structure and wording of the negative example. Strictly follows the fixed pattern and splits a single action into multiple list items.
3–4 (Penalty): Uses a fixed, list-based structure and several clichéd phrases, but the content splitting may not be as severe. Still feels very stiff and templated overall.
5–6 (Somewhat Penalized/Neutral): Avoids the most obvious stereotypes. May still use a list, but items correspond to distinct actions, not repetitive descriptions of a single action. Does not use phrases like “In the revised manuscript, we have taken...”
7–8 (Reward): Writing is natural and smooth. Does not use rigid numbered lists, but instead organically weaves the changes into the narrative. For example: “We have now corrected this number throughout the manuscript and clarified in the Methods section that...”
9–10 (Strong Reward): Excellent style. Completely avoids formulaic writing; language is confident, professional, and varied. Modifications are presented clearly in a narrative manner, making the response smooth and persuasive.
Output Format
Please provide your score and justification in the following only strict JSON format:
{
"diversity_score": <your score from 1 to 10>
}"""
def extract(answer,tag):
    matches = re.findall(rf'<{tag}>(.*?)</{tag}>', answer,re.DOTALL)
    return matches[0] if matches else None
def extract1(answer):
    matches = re.findall(r'```json(.*?)```', answer,re.DOTALL)
    return matches[0] if matches else answer
def call_api2(sys,prompt,model,client):
    for attempt in range(10):
        try:
            response = client.chat.completions.create(
                        model=model,
                        messages=[{"role": "system", "content": sys},
                               {"role": "user", "content": prompt},],
                        max_tokens=8000,
                        ),
            #print(response)
            output = response[0].choices[0].message.content 
            break
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < 9:
                time.sleep(1)  # Wait before retrying
            else:
                print("All attempts failed.")

    return output
def call_api1(sys,prompt,model,client):
    for attempt in range(10):
        try:
            response = client.chat.completions.create(
                        model=model,
                        messages=[{"role": "system", "content": sys},
                               {"role": "user", "content": prompt},],
                        max_tokens=20000,
                        temperature=0.7,
                        top_p=0.8,
                        presence_penalty=1.5,
                        extra_body={
                                    "top_k": 20, 
                                    "chat_template_kwargs": {"enable_thinking": False},
                                                                                        },
                        ),
            #print(response)
            output = response[0].choices[0].message.content 
            break
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < 9:
                time.sleep(1)  # Wait before retrying
            else:
                print("All attempts failed.")

    return output



def extract_tag_content_regex(input: str, tag: str, /, flags: int = re.S):
    # (?i) 大小写不敏感;  (?:\s[^>]*)? 匹配可能存在的属性;  (.*?) 懒惰匹配内容
    pattern = rf'(?i)<{tag}(?:\s[^>]*)?>(.*?)</{tag}>'
    return re.findall(pattern, input, flags)[0]
def reward1(response):

    def has_block(text: str,tag:str) -> bool:
        start = text.find(f"<{tag}>")
        end = text.find(f"</{tag}>")
        return start != -1 and end != -1 and end > start
    return has_block(response,"analysis") and has_block(response,"strategy") and has_block(response,"response")





def reward2(response,gold,model ="/project/airesearch/zongwei/model/rebuttal_agent"):
    if reward1(response) == 0:
        return 0
    client = OpenAI(
    base_url='https://api.nuwaapi.com/v1',
#     # sk-xxx替换为自己的key
    api_key='sk-HpN4ocRankRuValcM4lW18pfEd4403e0xoAUgOFI1np4GsEW',
 )
    client1 = OpenAI(
            base_url="http://localhost:8001/v1",
            api_key="EMPTY", 
            )
    prompt = "The gold analysis is: " + extract_tag_content_regex(gold,"analysis") + "The input analysis is:" + extract_tag_content_regex(response,"analysis") + "The gold strategy is: " + extract_tag_content_regex(gold,"strategy") + "The input strategy is:" + extract_tag_content_regex(response,"strategy")  
    for attempt in range(10):
        try:
            score = call_api1(SYS7,prompt,model,client1)
            s = json.loads(score)
            normalized = ((s["analysis_score"]-1.0)/9.0 + (s["strategy_score"]-1.0)/9.0)/2.0
            break
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < 9:
                time.sleep(1)  # Wait before retrying
            else:
                print("All attempts failed.")
                normalized = 0.0

    #print(normalized)
    #print(f"strategy score is{normalized}")
    return normalized


    




def reward3(inp, response, model="/project/airesearch/zongwei/model/rebuttal_agent"):
    """
    使用给定的 model 生成 4 个维度（1-10）的打分，并返回一个归一化到 [0, 1] 的总分。
    - 归一化方法：先对每个维度做 (score - 1) / 9 映射到 [0,1]，再取均值。
    - 你可以将 get_model_scores 替换为你的真实打分调用。
    """
    # 占位：请替换为你实际的模型打分接口，需返回长度为 4 的可迭代对象，元素在 [1,10]
    if reward1(response) == 0:
        return 0
    def get_model_scores(inp, response, model):
        client = OpenAI(
            base_url="http://localhost:8001/v1",
            api_key="EMPTY", 
            )
        comment_text = call_api1(SYS4, inp + "The response is:" + extract_tag_content_regex(response,"response") ,model,client)
        s = json.loads(extract1(comment_text))
        score = s.get("score",{})
        return [score["Attitude"],score["Clarity"],score["Persuasiveness"],score["Constructiveness"]]
    for attempt in range(10):
        try:
            scores = get_model_scores(inp, response, model)
            break
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < 9:
                time.sleep(1)  # Wait before retrying
            else:
                print("All attempts failed.")
                scores = [1,1,1,1]

    # 基本校验
    if not hasattr(scores, "__iter__"):
        raise ValueError("Model must return an iterable of 4 scores.")
    scores = list(scores)
    if len(scores) != 4:
        raise ValueError(f"Expected 4 scores, got {len(scores)}.")
    for i, s in enumerate(scores):
        try:
            s = float(s)
        except Exception as e:
            raise ValueError(f"Score at index {i} is not a number: {scores[i]!r}") from e
        scores[i] = s

    # 逐维归一化到 [0,1]
    norm_scores = [(s - 0) / 10 for s in scores]  # 1->0, 10->1

    # 聚合：取均值作为最终归一化分
    normalized = sum(norm_scores) / 4.0
    #print(f"response score is {normalized}")
    #print(normalized)
    return normalized

def reward4(response,model ="/project/airesearch/zongwei/model/rebuttal_agent"):
    if reward1(response) == 0:
        return 0
    client = OpenAI(
    base_url='https://api.nuwaapi.com/v1',
#     # sk-xxx替换为自己的key
    api_key='sk-HpN4ocRankRuValcM4lW18pfEd4403e0xoAUgOFI1np4GsEW',
 )
    client1 = OpenAI(
            base_url="http://localhost:8001/v1",
            api_key="EMPTY", 
            )
    prompt = extract_tag_content_regex(response,"response") 
    for attempt in range(10):
        try:
            score = call_api1(Diversity,prompt,model,client1)
            s = json.loads(score)
            normalized = (s["diversity_score"]-1.0)/9.0
            break
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < 9:
                time.sleep(1)  # Wait before retrying
            else:
                print("All attempts failed.")
                normalized = 0.0

    #print(normalized)
    #print(f"strategy score is{normalized}")
    return normalized

def compute_score_single(data_source,solution_str,ground_truth,extra_info):
    #print(solution_str)
    #print(ground_truth)
    return 0.1*reward1(solution_str)+0.3*reward2(solution_str,ground_truth)+0.3*reward3(extra_info["input"],solution_str)+0.3*reward4(solution_str)
    #return 0.2*reward1(solution_str)+0.4*reward2(solution_str,ground_truth)+0.4*reward4(solution_str)
    #return 0.2*reward1(solution_str)+0.8*reward2(solution_str,ground_truth)

def compute_score(data_sources,solution_strs,ground_truths,extra_infos,max_workers: int = 32,use_tqdm: bool = True):
    n = len(solution_strs)
    scores = [None] * n

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(compute_score_single, ds, ss, gt, ei): idx
            for idx, (ds, ss, gt, ei) in enumerate(
                zip(data_sources, solution_strs, ground_truths, extra_infos))
        }

        # --- 进度监控区 --------------------------------------------------
        print("显示进度")
        if use_tqdm:
            iterator = tqdm(as_completed(futures),
                            total=len(futures),
                            desc="Scoring",
                            unit="sample")
        else:
            iterator = as_completed(futures)
            done = 0
        # ---------------------------------------------------------------

        for fut in iterator:
            idx = futures[fut]
            try:
                scores[idx] = fut.result()
            except Exception as e:
                print(f"sample #{idx} failed: {e}")
                scores[idx] = 0.0

            if not use_tqdm:
                done += 1
                if done % 50 == 0 or done == n:           # 每 50 条更新一次
                    pct = done / n * 100
                    print(f"[{time.strftime('%X')}] {done}/{n}  ({pct:5.1f}%) done")

    return scores#import agent_prompt as ap
#import agent_framework1 as ag
from openai import OpenAI
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm 


SYS4 = """ You are a seasoned academic reviewer and response optimization expert. Your task is to evaluate the quality of the response based on the review comments, paper fragments, and the authors' responses. Please strictly follow the requirements below, and output only the score.

Input variables:

review_content: Complete content of the review comments. similar_paper_fragments: Best paper fragment most relevant to the comment. comment: Specific segment of the review comments. original_response: The authors' original response text to the comment.

Your task: Based on the input information, output only a JSON object containing the following item:
Scoring Standard
Score Range: 0 - 10
0: Wholly Ineffective
1-2: Perfunctory
3-4: Unconvincing
5-6: Addresses Some Concerns
7-8: Exceptional
9-10: Outstanding
score: Four-dimensional score breakdown, ranging from 0-10, structured as follows:
Attitude: The tone and professionalism of the response. 
Clarity: The logic, structure, and focus of the response.
Persuasiveness: The effectiveness of the argumentation and evidence support. 
Constructiveness: The commitment to revisions and specific actions taken.

Output requirements:

Only output the JSON object; do not include any other characters or explanations.
The scoring must be reasonable. 
All output must be in formal, polite academic English.
Your output must be strictly JSON formal which can be dirctly loaded by json.load()
Output format example:
{ "score": { "Attitude": <int>,
              "Clarity": <int>, 
              "Persuasiveness": <int>,
              "Constructiveness": <int> } """
SYS7 = """You are an evaluator. Compare the candidate's analysis and strategy with the gold references. Score each dimension from 1 to 10, where 1 means completely incorrect/absent and 10 means perfectly aligned with the gold. Return ONLY a single JSON object, no extra text.

Instructions:
1) Read the gold analysis and gold strategy as the ground truth.
2) Read the candidate analysis and candidate strategy.
3) Score each dimension independently using the following anchor criteria and ranges:

   For analysis_score (1-10):
   - 10-band [9.5, 10.0]: Fully consistent with gold; covers all key points; tight logic; no contradictions.
   - 8-band  [7.0,  9.4]: Mostly consistent; minor omissions or small inaccuracies.
   - 5-band  [3.5,  6.9]: Partial alignment; notable gaps or some incorrect reasoning.
   - 2-band  [1.5,  3.4]: Largely misaligned; major omissions; flawed logic.
   - 1-band  [1.0,  1.4]: Completely wrong, irrelevant, or missing.

   For strategy_score (1-10):
   - 10-band [9.5, 10.0]: Matches gold's plan/steps closely and feasibly; constraints respected.
   - 8-band  [7.0,  9.4]: Mostly matches; minor deviations that don't harm feasibility.
   - 5-band  [3.5,  6.9]: Partial match; important steps missing or order problematic.
   - 2-band  [1.5,  3.4]: Poor match; infeasible or contradicts key constraints.
   - 1-band  [1.0,  1.4]: No strategy or entirely misaligned.

4) Scoring guidance:
   - Choose the appropriate band first, then pick a specific number within the band based on severity/coverage.
   - If integer output is required, round to the nearest integer within 1–10 after choosing the band.
   - Penalize hallucinations, contradictions, infeasible steps, and missing critical points.
   - Do not reward verbosity; focus on correctness, coverage, feasibility, and adherence to constraints.

Output format:
Return ONLY this JSON (no Markdown, no backticks):
{
  "analysis_score": <number 1-10>,
  "strategy_score": <number 1-10>
}
"""
Diversity = """Role

You are an experienced academic reviewer and AI linguist. Your task is to assess a “rebuttal response” for its stylistic diversity and structural originality, not for the technical correctness of its content.
Core Task
You will be given a response to evaluate. Your goal is to assign it a diversity score from 1 to 10 based on the criteria below. Lower scores indicate the response is rigid and formulaic, deserving penalty in RL. Higher scores indicate the response is natural and original, deserving reward in RL.
Negative Example to Penalize

Below is a typical, low-diversity response that should be penalized. Its structure and wording are very rigid.
We thank the reviewer for this important observation and fully agree that the necessity of training 200,000 models was both misleading and inconsistent with prior work. In the revised manuscript, we have taken the following actions in direct response to this comment:
We have corrected all instances where the number 200,000 models is mentioned...
We have explicitly stated in the revised Methods section...
We have added a clarifying sentence in Section 4...
We have revised all figure captions and text...
We have included a statement in the revised Limitations section...
We believe these changes fully address the reviewer's concern... We thank the reviewer again for this helpful suggestion...
Key Characteristics to Penalize
When assigning a score, pay special attention to the following three aspects. If the response exhibits these traits, assign a lower score:
Overly Rigid Structure: Does the response strictly follow the pattern [Thanking] → [Fixed phrase introducing list] → [Numbered or bulleted list] → [Summary phrase]?
Redundant Splitting of a Single Task: Does the response artificially split a single, complete action (e.g., “I corrected a typo”) into multiple list items to inflate the list? In the negative example above, the single action of “correcting the number 200,000” is split into five separate points, which is a poor style.
Use of Cliché Phrases: Does the response frequently use the following or similar stock phrases?
"In the revised manuscript, we have taken the following actions..."
"In direct response to this comment..."
"We believe these changes fully address the reviewer's concern..."
Scoring Rubric – 1-10 Scale
1–2 (Severe Penalty): Nearly copies the structure and wording of the negative example. Strictly follows the fixed pattern and splits a single action into multiple list items.
3–4 (Penalty): Uses a fixed, list-based structure and several clichéd phrases, but the content splitting may not be as severe. Still feels very stiff and templated overall.
5–6 (Somewhat Penalized/Neutral): Avoids the most obvious stereotypes. May still use a list, but items correspond to distinct actions, not repetitive descriptions of a single action. Does not use phrases like “In the revised manuscript, we have taken...”
7–8 (Reward): Writing is natural and smooth. Does not use rigid numbered lists, but instead organically weaves the changes into the narrative. For example: “We have now corrected this number throughout the manuscript and clarified in the Methods section that...”
9–10 (Strong Reward): Excellent style. Completely avoids formulaic writing; language is confident, professional, and varied. Modifications are presented clearly in a narrative manner, making the response smooth and persuasive.
Output Format
Please provide your score and justification in the following only strict JSON format:
{
"diversity_score": <your score from 1 to 10>
}"""
def extract(answer,tag):
    matches = re.findall(rf'<{tag}>(.*?)</{tag}>', answer,re.DOTALL)
    return matches[0] if matches else None
def extract1(answer):
    matches = re.findall(r'```json(.*?)```', answer,re.DOTALL)
    return matches[0] if matches else answer
def call_api2(sys,prompt,model,client):
    for attempt in range(10):
        try:
            response = client.chat.completions.create(
                        model=model,
                        messages=[{"role": "system", "content": sys},
                               {"role": "user", "content": prompt},],
                        max_tokens=8000,
                        ),
            #print(response)
            output = response[0].choices[0].message.content 
            break
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < 9:
                time.sleep(1)  # Wait before retrying
            else:
                print("All attempts failed.")

    return output
def call_api1(sys,prompt,model,client):
    for attempt in range(10):
        try:
            response = client.chat.completions.create(
                        model=model,
                        messages=[{"role": "system", "content": sys},
                               {"role": "user", "content": prompt},],
                        max_tokens=20000,
                        temperature=0.7,
                        top_p=0.8,
                        presence_penalty=1.5,
                        extra_body={
                                    "top_k": 20, 
                                    "chat_template_kwargs": {"enable_thinking": False},
                                                                                        },
                        ),
            #print(response)
            output = response[0].choices[0].message.content 
            break
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < 9:
                time.sleep(1)  # Wait before retrying
            else:
                print("All attempts failed.")

    return output



def extract_tag_content_regex(input: str, tag: str, /, flags: int = re.S):
    # (?i) 大小写不敏感;  (?:\s[^>]*)? 匹配可能存在的属性;  (.*?) 懒惰匹配内容
    pattern = rf'(?i)<{tag}(?:\s[^>]*)?>(.*?)</{tag}>'
    return re.findall(pattern, input, flags)[0]
def reward1(response):

    def has_block(text: str,tag:str) -> bool:
        start = text.find(f"<{tag}>")
        end = text.find(f"</{tag}>")
        return start != -1 and end != -1 and end > start
    return has_block(response,"analysis") and has_block(response,"strategy") and has_block(response,"response")





def reward2(response,gold,model ="/project/airesearch/zongwei/model/rebuttal_agent"):
    if reward1(response) == 0:
        return 0
    client = OpenAI(
    base_url='https://api.nuwaapi.com/v1',
#     # sk-xxx替换为自己的key
    api_key='',
 )
    client1 = OpenAI(
            base_url="http://localhost:8001/v1",
            api_key="EMPTY", 
            )
    prompt = "The gold analysis is: " + extract_tag_content_regex(gold,"analysis") + "The input analysis is:" + extract_tag_content_regex(response,"analysis") + "The gold strategy is: " + extract_tag_content_regex(gold,"strategy") + "The input strategy is:" + extract_tag_content_regex(response,"strategy")  
    for attempt in range(10):
        try:
            score = call_api1(SYS7,prompt,model,client1)
            s = json.loads(score)
            normalized = ((s["analysis_score"]-1.0)/9.0 + (s["strategy_score"]-1.0)/9.0)/2.0
            break
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < 9:
                time.sleep(1)  # Wait before retrying
            else:
                print("All attempts failed.")
                normalized = 0.0

    #print(normalized)
    #print(f"strategy score is{normalized}")
    return normalized


    




def reward3(inp, response, model="/project/airesearch/zongwei/model/rebuttal_agent"):
    """
    使用给定的 model 生成 4 个维度（1-10）的打分，并返回一个归一化到 [0, 1] 的总分。
    - 归一化方法：先对每个维度做 (score - 1) / 9 映射到 [0,1]，再取均值。
    - 你可以将 get_model_scores 替换为你的真实打分调用。
    """
    # 占位：请替换为你实际的模型打分接口，需返回长度为 4 的可迭代对象，元素在 [1,10]
    if reward1(response) == 0:
        return 0
    def get_model_scores(inp, response, model):
        client = OpenAI(
            base_url="http://localhost:8001/v1",
            api_key="EMPTY", 
            )
        comment_text = call_api1(SYS4, inp + "The response is:" + extract_tag_content_regex(response,"response") ,model,client)
        s = json.loads(extract1(comment_text))
        score = s.get("score",{})
        return [score["Attitude"],score["Clarity"],score["Persuasiveness"],score["Constructiveness"]]
    for attempt in range(10):
        try:
            scores = get_model_scores(inp, response, model)
            break
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < 9:
                time.sleep(1)  # Wait before retrying
            else:
                print("All attempts failed.")
                scores = [1,1,1,1]

    # 基本校验
    if not hasattr(scores, "__iter__"):
        raise ValueError("Model must return an iterable of 4 scores.")
    scores = list(scores)
    if len(scores) != 4:
        raise ValueError(f"Expected 4 scores, got {len(scores)}.")
    for i, s in enumerate(scores):
        try:
            s = float(s)
        except Exception as e:
            raise ValueError(f"Score at index {i} is not a number: {scores[i]!r}") from e
        scores[i] = s

    # 逐维归一化到 [0,1]
    norm_scores = [(s - 0) / 10 for s in scores]  # 1->0, 10->1

    # 聚合：取均值作为最终归一化分
    normalized = sum(norm_scores) / 4.0
    #print(f"response score is {normalized}")
    #print(normalized)
    return normalized

def reward4(response,model ="/project/airesearch/zongwei/model/rebuttal_agent"):
    if reward1(response) == 0:
        return 0
    client = OpenAI(
    base_url='https://api.nuwaapi.com/v1',
#     # sk-xxx替换为自己的key
    api_key='sk-HpN4ocRankRuValcM4lW18pfEd4403e0xoAUgOFI1np4GsEW',
 )
    client1 = OpenAI(
            base_url="http://localhost:8001/v1",
            api_key="EMPTY", 
            )
    prompt = extract_tag_content_regex(response,"response") 
    for attempt in range(10):
        try:
            score = call_api1(Diversity,prompt,model,client1)
            s = json.loads(score)
            normalized = (s["diversity_score"]-1.0)/9.0
            break
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < 9:
                time.sleep(1)  # Wait before retrying
            else:
                print("All attempts failed.")
                normalized = 0.0

    #print(normalized)
    #print(f"strategy score is{normalized}")
    return normalized

def compute_score_single(data_source,solution_str,ground_truth,extra_info):
    #print(solution_str)
    #print(ground_truth)
    return 0.1*reward1(solution_str)+0.3*reward2(solution_str,ground_truth)+0.3*reward3(extra_info["input"],solution_str)+0.3*reward4(solution_str)
    #return 0.2*reward1(solution_str)+0.4*reward2(solution_str,ground_truth)+0.4*reward4(solution_str)
    #return 0.2*reward1(solution_str)+0.8*reward2(solution_str,ground_truth)

def compute_score(data_sources,solution_strs,ground_truths,extra_infos,max_workers: int = 32,use_tqdm: bool = True):
    n = len(solution_strs)
    scores = [None] * n

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(compute_score_single, ds, ss, gt, ei): idx
            for idx, (ds, ss, gt, ei) in enumerate(
                zip(data_sources, solution_strs, ground_truths, extra_infos))
        }

        # --- 进度监控区 --------------------------------------------------
        print("显示进度")
        if use_tqdm:
            iterator = tqdm(as_completed(futures),
                            total=len(futures),
                            desc="Scoring",
                            unit="sample")
        else:
            iterator = as_completed(futures)
            done = 0
        # ---------------------------------------------------------------

        for fut in iterator:
            idx = futures[fut]
            try:
                scores[idx] = fut.result()
            except Exception as e:
                print(f"sample #{idx} failed: {e}")
                scores[idx] = 0.0

            if not use_tqdm:
                done += 1
                if done % 50 == 0 or done == n:           # 每 50 条更新一次
                    pct = done / n * 100
                    print(f"[{time.strftime('%X')}] {done}/{n}  ({pct:5.1f}%) done")

    return scores