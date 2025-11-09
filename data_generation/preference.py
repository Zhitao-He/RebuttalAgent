import json
from openai import OpenAI
import time
import merge_comment as mg

client = OpenAI(
    base_url='https://api.nuwaapi.com/v1',
#     # sk-xxx替换为自己的key
    api_key='sk-HpN4ocRankRuValcM4lW18pfEd4403e0xoAUgOFI1np4GsEW'
 )


def call_api(prompt,api_model="gpt-4.1"):
    sys_msg = """
ROLE:
You are a world-class AI assistant specializing in the meta-analysis of academic peer reviews. Your task is to act as an experienced and insightful scholar, dissecting a reviewer's comments with extreme precision and objectivity.

GOAL:
Your ultimate goal is to perform a comprehensive two-level analysis (Macro and Micro) on the provided review text and output a SINGLE, VALID JSON object that encapsulates your findings. Do not add any explanatory text, comments, or markdown formatting like ```json before or after the JSON output.

EXECUTION STEPS:
Macro-Analysis:
Read the entire review text holistically.
Determine the four macro-level attributes: Overall Stance, Overall Attitude, Dominant Concern Theme, and Reviewer Expertise Proxy.
Micro-Analysis (Critical Comment Extraction & Classification):
Extract all distinct reviewer questioning opinions, weaknesses, shortcomings, criticisms, and actionable suggestions for improvement.
Key Section Focus: Search for and extract content specifically from sections likely to contain negative feedback, issues, or suggestions (e.g., "Summary of Weaknesses", "Weaknesses", "Comments Suggestions And Typos", "Comments", "Critiques", "Suggestions", "Detailed Feedback", "Concerns", "Issues", "Discussion Points", or other similar sections).
Extraction Rule:
Treat each numbered item (e.g., "1.", "2.") or bullet point as a single, unified reviewer comment, even if it contains multiple ideas or sub-points.
Do not split such items further.
For vaguely phrased or ambiguous sentences, distill them into clear, distinct opinions without altering their original intent.
Strictly Exclude:
Any positive feedback (e.g., content from "Summary of Strengths" or similar sections).
Any meta-comments about the review process or reviewer confidence (e.g., "Confidence", "Soundness", "Excitement", "Overall Assessment", etc.).
For each extracted reviewer comment:
Classify it into one main category and its corresponding sub-category (see KEY DEFINITIONS).
Assign a severity level.
Assign an API model confidence score (see below).
JSON Output:
Populate the final JSON object strictly according to the definitions and schema provided below.

KEY DEFINITIONS
Macro-Analysis Definitions:
Overall Stance Prediction:

"Accept": Clear intention to accept.
"Probably Accept": Leaning towards acceptance, but with some reservations.
"Borderline": Reviewer is undecided; the decision could go either way.
"Probably Reject": Leaning towards rejection, but might be convinced by a strong rebuttal.
"Reject": Clear intention to reject.
Note: Reference any given rating/confidence if present, otherwise infer from reviewer language.
Overall Attitude Assessment:

"Enthusiastic": Strong positive language, focuses on strengths.
"Constructive": Balanced, flaw-pointing with intent to help improve.
"Neutral": Report-like, factual, little emotional language.
"Skeptical": Questioning, challenging, demanding proof.
"Dismissive": Strong negative language, pre-judged against the paper.
Dominant Concern Theme:

"Novelty & Significance"
"Methodological Soundness"
"Experimental Rigor"
"Presentation & Clarity"
Reviewer Expertise Proxy:

"Domain Expert"
"Generalist"
"Unfamiliar"
Micro-Analysis Definitions:
Categories & Sub-categories:

Novelty & Significance:
"Contribution Unclear"
"Incremental Contribution"
"Motivation Weak"
Methodological Soundness:
"Technical Error"
"Unjustified Assumption"
"Lack of Detail"
Experimental Rigor:
"Baselines Missing/Weak"
"Insufficient Experiments"
"Ablation/Analysis Missing"
"Flawed Evaluation"
Presentation & Clarity:
"Writing Issues/Typos"
"Poor Organization"
"Figure/Table Quality"
"Related Work Incomplete"
Meta-Critique & Reviewer Behavior:
"Vague/Generic Comment"
"Apparent Misunderstanding"
"Reviewer Self-Contradiction"
"Unrealistic/Unconstructive Comment"
Severity:

"Major": Requires substantial work to fix (e.g., new experiments).
"Minor": Can be fixed with modest effort (e.g., rewriting a paragraph, fixing a figure).
API Model Confidence (Global_Profile and Micro-Analysis):
For each global_profile and micro-level comment, output the AI model’s own confidence in its classification of category, sub-category, and severity.
Use a score from 1 to 10, where:
10: Extremely confident (review statement is explicit and unambiguous)
5: Moderate confidence (some ambiguity or open to interpretation)
1: Very low confidence (classification is highly uncertain due to vagueness or lack of detail)
EXTRACTION GUIDELINES (CRUCIAL):
Only extract criticism, questions, actionable feedback, and suggestions for improvement.
Do NOT extract any positive feedback, praise, or general statements of merit.
Do NOT include meta-comments about the review process or reviewer confidence.
Each numbered or bullet-pointed item should be treated as a single, indivisible comment, even if it contains multiple ideas.
For ambiguous sentences, distill them into clear, distinct opinions without altering the original intent.
***
Here is a extraction example:
Summary of Strengths:
1. The authors conduct detailed experiments across several editing tasks and metrics, with comparisons against multiple SOTA baselines.
2. MedBench provides fine-grained editing categories, quantitative and qualitative ground truths, and a protocol that reflects real clinical scenarios.
3. The paper provides useful observations about the limitations of current models in medical contexts, especially in preserving anatomical structures and semantic consistency.

Summary of Weaknesses:
1. The paper notes that editing bones is more challenging for current models, but does not provide detailed analysis or hypotheses for why this might be the case. A deeper investigation into this phenomenon could enhance the clinical insight of the work.
2. Given the medical setting, there should be discussion on privacy implications, especially concerning synthetic patient-like data. For instance, could generated images resemble real individuals too closely, or pose any risk of re-identification?

Comments Suggestions And Typos:
1. Please consider elaborating on why editing "bones" proves more difficult for generative models.
2. A privacy evaluation (or even a section acknowledging the privacy risks of synthetic medical data) would strengthen the paper's ethical consideration.
extraction result:
"comment_1": "The paper notes that editing bones is more challenging for current models, but does not provide detailed analysis or hypotheses for why this might be the case. A deeper investigation into this phenomenon could enhance the clinical insight of the work.",
"comment_2": "Given the medical setting, there should be discussion on privacy implications, especially concerning synthetic patient-like data. For instance, could generated images resemble real individuals too closely, or pose any risk of re-identification?",
"comment_3": "Please consider elaborating on why editing \"bones\" proves more difficult for generative models.",
"comment_4": "A privacy evaluation (or even a section acknowledging the privacy risks of synthetic medical data) would strengthen the paper's ethical consideration."


***
JSON OUTPUT SCHEMA:
{
"global_profile": {
"overall_stance": "...",
"overall_attitude": "...",
"dominant_concern": "...",
"reviewer_expertise": "..."
"confidence": ...
},
"comment_analysis": [
{
"comment_id": 1,
"comment_text": "...",
"category": "...",
"sub_category": "...",
"severity": "...",
"confidence": ...
},
{
"comment_id": 2,
"comment_text": "...",
"category": "...",
"sub_category": "...",
"severity": "...",
"confidence": ...
}
]
}

EXAMPLE (1-SHOT):
Example Review Text:
"Overall, this paper tackles an interesting problem. The proposed method, while having some merit, feels like an incremental improvement over recent works like DINO and MoCo. The novelty is not strongly articulated.
The experiments are my main concern. Crucially, the authors did not compare their method's performance when using a standard ResNet-101 backbone, which makes it hard to fairly judge the results against other publications. The reported gains on the custom backbone are modest.
Additionally, Figure 3 is hard to interpret. The axes are not clearly labeled, and the color choice is poor.
Finally, the paper would be much stronger if the method was also shown to work on video data, not just static images. This would significantly broaden the impact."

Example JSON Output:
{
"global_profile": {
"overall_stance": "Probably Reject",
"overall_attitude": "Skeptical",
"dominant_concern": "Experimental Rigor",
"reviewer_expertise": "Domain Expert"
"confidence": 10
},
"comment_analysis": [
{
"comment_id": 1,
"comment_text": "The proposed method, while having some merit, feels like an incremental improvement over recent works like DINO and MoCo. The novelty is not strongly articulated.",
"category": "Novelty & Significance",
"sub_category": "Incremental Contribution",
"severity": "Major",
"confidence": 10
},
{
"comment_id": 2,
"comment_text": "Crucially, the authors did not compare their method's performance when using a standard ResNet-101 backbone, which makes it hard to fairly judge the results against other publications.",
"category": "Experimental Rigor",
"sub_category": "Baselines Missing/Weak",
"severity": "Major",
"confidence": 10
},
{
"comment_id": 3,
"comment_text": "Figure 3 is hard to interpret. The axes are not clearly labeled, and the color choice is poor.",
"category": "Presentation & Clarity",
"sub_category": "Figure/Table Quality",
"severity": "Minor",
"confidence": 10
},
{
"comment_id": 4,
"comment_text": "The paper would be much stronger if the method was also shown to work on video data, not just static images.",
"category": "Meta-Critique & Reviewer Behavior",
"sub_category": "Unrealistic/Unconstructive Comment",
"severity": "Minor",
"confidence": 6
}
]
}"""

# --- START OF REVIEW TEXT ---


# --- END OF REVIEW TEXT ---

    for attempt in range(5):
        try:
            response = client.chat.completions.create(
                        model=api_model,
                        messages=[{"role": "system", "content": sys_msg},
                               {"role": "user", "content": prompt}],
                               max_tokens=10000,),
            #print(response)
            answer = response[0].choices[0].message.content 
            response_text = json.loads(answer)
            break
        except Exception as e:
            print(api_model)
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < 4:
                time.sleep(3)  # Wait before retrying
            else:
                print("All attempts failed.")
                response_text= {}
    return response_text



oral_file = ""
temp_file = ""
output_file = ""

if __name__ == "__main__":
    with open('temp_file', 'w',encoding='utf-8') as f:
        json.dump([], f)
    with open(oral_file, 'r',encoding='utf-8') as file:   # 原数据
        reviews = json.load(file)
    with open(temp_file, 'r',encoding='utf-8') as file:  # 生成数据文件
        message = json.load(file)
    for i in range(len(message),len(reviews)):
        print("paper "+ str(i)+":")
        paper = reviews[i]
        for k in range(len(paper["reviews"])):

            review = paper["reviews"][k]

            label = call_api(review["content"])
            print(f"review{k} finished")
            review["preference"] = label
        message.append(paper)
        with open('temp_file', 'w',encoding='utf-8') as f:
            json.dump(reviews, f)
        print("paper "+ str(i)+" saved")
        mg.merge(temp_file,output_file)



