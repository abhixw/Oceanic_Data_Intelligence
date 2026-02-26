import io
import base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_experimental.agents import create_pandas_dataframe_agent
from data_loader import load_data

# Load environment variables
load_dotenv()

# Load dataset using absolute path
import os
base_path = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(base_path, "../data/train.csv")
df = load_data(data_path)

# Initialize Groq LLM (70b models are much more accurate for reasoning and tool-calling)
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0
)

# Consolidate instructions into PREFIX to handle professional data analysis and STT transcription
PREFIX = """
You are a professional Data Analyst working with the Titanic dataset.
The user's question comes from speech-to-text transcription.
It may include filler words, grammar mistakes, or conversational phrasing.
Interpret the intent accurately but do not mention that the input came from speech.

The variable `df` is already loaded and contains all 891 Titanic records.
DO NOT attempt to redefine `df` or manually create data.

STRICT RULES:
1. Use ONLY the columns that exist in the dataset: {list(df.columns)}
2. For ANY numerical, statistical, or percentage question:
   - YOU MUST perform the calculation using a python code block.
   - YOU MUST explicitly read the numeric output of the code.
   - NEVER do math in your head. 
   - Report the EXACT numbers returned by the tool output in your Final Answer.
3. Your text summary MUST match the results returned by your code execution exactly. Hallucinating numbers or denominators is a critical failure.
4. For charts, use matplotlib/seaborn and include the exact numerical counts from the data in your Final Answer.
5. For pie charts, use `plt.pie()` with `autopct='%1.1f%%'`.
6. For bar charts, use `ax.bar_label()`.
7. NEVER include python code blocks in your Final Answer.
8. If the question is unclear, ask a short clarification question.
9. Be concise and professional.

Respond in a professional, clean, data-focused style.
"""

# Create agent using ReAct logic for better stability on Groq/Llama 3
# Note: ReAct (zero-shot-react-description) is generally more reliable than tool-calling for these models
agent = create_pandas_dataframe_agent(
    llm,
    df,
    verbose=True,
    allow_dangerous_code=True,
    agent_type="zero-shot-react-description",
    max_iterations=15,
    include_df_in_prompt=False,
    agent_executor_kwargs={"handle_parsing_errors": True}
)

def run_query(user_query: str):
    try:
        plt.close("all")

        response = agent.invoke({"input": user_query})

        image_base64 = None

        if plt.get_fignums():
            buffer = io.BytesIO()
            plt.savefig(buffer, format="png")
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode("utf-8")
            plt.close("all")

        return {
            "answer": response["output"],
            "image": image_base64
        }

    except Exception as e:
        return {
            "answer": f"Error processing query: {str(e)}",
            "image": None
        }