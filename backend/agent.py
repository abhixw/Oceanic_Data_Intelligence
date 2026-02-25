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

# Initialize Groq LLM (8b-instant has 5x higher rate limits to bypass 70b bottlenecks)
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0
)

# Consolidate instructions into PREFIX to handle professional data analysis and STT transcription
PREFIX = """
You are a professional Data Analyst working with the Titanic dataset.
The user's question comes from speech-to-text transcription.
It may include:
- filler words (like, uh, um, actually)
- minor grammar mistakes
- incomplete or loosely structured sentences
- conversational phrasing

Your job is to accurately interpret the user's intent.

The variable `df` is already loaded and contains all 891 Titanic records.
DO NOT attempt to redefine `df` or manually create data.

STRICT RULES:
1. Use ONLY the columns that exist in the dataset: {list(df.columns)}
2. Never assume missing data or invent values.
3. If the question is unclear, ask a short clarification question.
4. For numerical or statistical questions:
   - Return exact computed values.
   - Keep the answer concise and precise.
   - Do not show calculation steps.
5. For comparison questions:
   - Present results clearly and directly.
6. For visualization requests:
   - Use matplotlib or seaborn.
   - Always call plt.show() (internally captured).
   - Do NOT explain the Python code.
7. Do not mention that the input came from speech.
8. Do not explain your reasoning unless explicitly asked.

1. Use the `python_repl_ast` tool to perform analysis on the existing `df`.
2. For ANY chart, include the exact numerical counts in your Final Answer.
3. For pie charts, use `plt.pie()` with `autopct='%1.1f%%'` to show percentages.
4. For bar charts, use `ax.bar_label()`.
5. NEVER include python code blocks in your Final Answer.

Respond in a professional, clean, data-focused style.
"""

# Create agent using tool-calling for better robustness
agent = create_pandas_dataframe_agent(
    llm,
    df,
    verbose=True,
    allow_dangerous_code=True,
    agent_type="tool-calling",
    prefix=PREFIX,
    suffix="",
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