import json
import random

SYS=""" You are an expert academic assistant specializing in crafting persuasive and respectful rebuttals for peer reviews. Your goal is to formulate a response that addresses the reviewer's concerns directly and constructively, ultimately strengthening the paper's position for acceptance. You receive the following inputs:

Full_Review_Content: The entire review text for the target paper.
Target_Comment: A specific excerpt from the review that requires a response.
Relevant_Paper_Fragment: A key excerpt from the author's own manuscript. This fragment provides the essential context and technical details that relevant to the Target_Comment.

Your task is to generate a structured rebuttal plan and response by following these steps precisely:

Step 1: Analysis 
First, conduct your analysis of the overall review and target comment. Present this analysis inside <analysis> and </analysis> tags using the strict JSON format specified below. 

Step 2: Rebuttal Strategy 
Based on your analysis and the information within the Relevant_Paper_Fragment, devise an optimal, step-by-step strategy for the response. Present this strategy as a numbered list inside <strategy> and </strategy> tags. Each step should be a clear action.

Step 3: Information Retrieval (Optional) If, and only if, the information required to form a response is not present in your knowledge base or the Relevant_Paper_Fragment (e.g., for papers published last month), specify necessary search keywords inside <retrieve>keyword1; keyword2; …</retrieve>. Otherwise, omit this section.

Step 4: Rebuttal Response 
Finally, craft the rebuttal response for the Target_Comment. Write the response inside <response> and </response>, based on your above analysis and strategy.

Here is an example of output format:

I need to analysis the review’s overall instance and the target comment: 
<analysis>
{
  "global_profile": {
    "overall_stance": "...",
    "overall_attitude": "...",
    "dominant_concern": "...",
    "reviewer_expertise": "..."
  },
  "comment_analysis": 
    {
      "comment_text": "...",
      "category": "...",
      "sub_category": "...",
      "severity": "..."
}
}
</analysis>.

Based on current overall analysis, to address the target comment, I need to adopt the following strategies:
<strategy> 1. ; 2. ; 3. ; XXX</strategy>.

(Optional, If and only if additional information beyond your knowledge is truly necessary) I need to retrieve some additional information to provide a more comprehensive response: <retrieve>keyword1; keyword2; …</retrieve>

Based on the above analysis and strategies, for the target comment: <response>XXX</response>."""

SYS1 = """You are a seasoned academic reviewer and response optimization expert. Your task is to evaluate the quality of the response based on the review comments, paper fragments, and the authors' responses. Please strictly follow the requirements below, and output only the score and score explanation.

Input variables:
1.Review_content: Complete content of the review comments.
2.Paper_fragment: Paper fragment most relevant to the comment. 
3.Target_comment: The target comment that currently needs to be addressed
4.Target_comment_response: The authors' original response text to the comment.

Your task: Based on the input information, output only a JSON object containing the following two items:
Scoring Standard: Score Range: 0 - 10 
0: Wholly Ineffective 
1-2: Perfunctory 3-4: Unconvincing 
5-6: Addresses Some Concerns 
7-8: Exceptional 
9-10: Outstanding

score: Four-dimensional score breakdown, ranging from 0-10, structured as follows: Attitude: The tone and professionalism of the response. Clarity: The logic, structure, and focus of the response. Persuasiveness: The effectiveness of the argumentation and evidence support. Constructiveness: The commitment to revisions and specific actions taken.

score_explanation: A brief explanation of each score, specifically citing key points from the response text that reflect the scores and any shortcomings.

Output requirements:

Only output the JSON object; do not include any other characters or explanations. The scoring must be reasonable, and the score explanation must clearly reference the original text that reflects the score. All output must be in formal, polite academic English.
Output format example:
{ "score": {  "Attitude": <int>, 
                 "Clarity": <int>, 
                 "Persuasiveness": <int>, 
                 "Constructiveness": <int> }, 
"score_explanation": <explanation for your given score> }"""

SYS2 = """You are an AI authors tasked with respond to review comments on your academic paper. Based on the following input variables, generate a thoughtful and professional response to the specific review comment.
Input Variables:
1.Review_content: Complete content of the review comments.
2.Paper_fragment: Paper fragment most relevant to the comment. 
3.Target_comment: The target comment that currently needs to be addressed

Response Requirements:

Address the reviewer’s concerns directly and respectfully.
According to the relevant paper fragment to support your response.
Clearly explain any changes made to the manuscript or provide justification if no changes were made.
Maintain a professional and constructive tone throughout the response.
Output Format: Your response should be a well-structured paragraph that clearly adress the target comment"""





def RA_input(comment):
    comment_content = "The comment content is：" +"\n" + comment["comment"]["comment_text"]+"\n"
    paper = "The best paper fragment is: " + comment["top5_text"][0] + "\n"
    review_content = "The whole review content is"+ "\n" + comment["review_content"] + "\n"
    input = review_content + comment_content + paper
    return input

def RW_input(comment):
    comment_content = "The comment content is:" +"\n" + comment["comment"]["comment_text"]+"\n"
    paper = "The best paper fragment is: " + comment["top5_text"][0] + "\n"
    review_content = "The whole review content is"+ "\n" + comment["review_content"] + "\n"
    re = "The original response fragment is"+"\n"+comment["refine"]["extracted_response_fragment"]+"\n"
    input = review_content + comment_content + re + paper
    return input
def RW_input1(comment):
    comment_content = "The comment content is:" +"\n" + comment["comment"]["comment_text"]+"\n"
    paper = "The best paper fragment is: " + comment["top5_text"][0] + "\n"
    review_content = "The whole review content is"+ "\n" + comment["review_content"] + "\n"
    re = "The original response fragment is"+"\n"+comment["response"]+"\n"
    input = review_content + comment_content + re + paper
    return input
def tag(string,tag):
    return f"<{tag}>"+string+f"</{tag}>"
def RA_output(comment):
    output = "I need to analysis the review’s overall instance and the target comment: "
    output += "\n"
    comment_analysis = comment["comment"].copy()
    del comment_analysis["comment_id"]
    output += tag(str(comment["global_profile"])+"\n"+str(comment_analysis),"analysis")
    output += "\n"
    output += "Based on current overall analysis, to address the target comment, I need to adopt the following strategies:"
    output += "\n"
    output += tag(str(comment["refine"]["strategy"]),"strategy")
    output += "\n"
    temp = ""
    retrieve = comment["refine"].get("retrieve") or False
    if retrieve:
        output  += " I need to retrieve some additional information to provide a more comprehensive response: "
        for query in comment["refine"]["retrieve_query"]:
            temp += str(query)
            temp += ";"
        output += tag(temp,"retrieve")
    output += "\n"
    output += "Based on the above analysis and strategies, for the target comment: "
    output += "\n"
    output += tag(comment["refine"]["refined_response"],"response")
    return 

def RW_output(comment):
    output = {}
    output["score"] = comment["refine"]["score"]
    output["explanation"] = comment["refine"]["score_explanation"]
    if isinstance(output, (dict, list)):
        output = json.dumps(
        output,
        ensure_ascii=False,           # 保留中文
        separators=(",", ":"),        # 去掉多余空格，省 token
    )
    return output
def gene_RA(file_name,output_name):
    with open(file_name,'r',encoding='utf-8') as file:   # 原数据
        data = json.load(file)

    messages = []
    for i in range(len(data)):
        comment = data[i]
        if "refine" not in comment or comment["refine"] == {}:
            continue
        content = {}
        content["instruction"] = SYS2
        content["input"] = RA_input(comment)
        #content["output"]= RA_output(comment)
        content["output"] = comment["refine"]["extracted_response_fragment"]
        messages.append(content)
    random.shuffle(messages)
    with open(output_name,'w',encoding='utf-8') as file:   # 原数据
        json.dump(messages,file)
    print(messages[0])
    print(len(messages))
    print("finish")


def gene_RW(file_name,output_name):
    with open(file_name,'r',encoding='utf-8') as file:   # 原数据
        data = json.load(file)

    messages = []
    for i in range(len(data)):
        comment = data[i]
        if "refine" not in comment or comment["refine"] == {}:
            continue
        if  comment["refine"]["exist_response"] == False:
            continue
        content = {}
        content["instruction"] = SYS1
        content["input"] = RW_input(comment)
        content["output"]= RW_output(comment)
        messages.append(content)

    with open(output_name,'w',encoding='utf-8') as file:   # 原数据
        json.dump(messages,file)
    print(len(messages))
    print("finish")
def gene_RW1(file_name,output_name):
    with open(file_name,'r',encoding='utf-8') as file:   # 原数据
        data = json.load(file)

    messages = []
    for i in range(len(data)):
        comment = data[i]
        if "refine" not in comment or comment["refine"] == {}:
            continue
        content = {}
        content["instruction"] = SYS1
        content["input"] = RW_input1(comment)
        content["output"]= RW_output(comment)
        messages.append(content)

    with open(output_name,'w',encoding='utf-8') as file:   # 原数据
        json.dump(messages,file)
    print(len(messages))
    print("finish")




gene_RA("ag_train.json","train/sft_oral.json")
#gene_RW("ag_score.json","train/ora_score.json")
#gene_RW1("merged.json","train/mix_score.json")

#with open("train/ora_score.json",'r',encoding='utf-8') as file:   # 原数据
    #data1 = json.load(file)
#with open("train/mix_score.json",'r',encoding='utf-8') as file:   # 原数据
    #data2 = json.load(file)

#data = data1+data2

#with open("train/reward_model.json",'w',encoding='utf-8') as file:   # 原数据
#    json.dump(data,file)
#print(len(data))
#print("finish")
