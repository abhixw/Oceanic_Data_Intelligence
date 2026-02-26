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

# Instructions into PREFIX to handle professional data analysis and STT transcription
column_names = list(df.columns)
PREFIX = f"""
You are a professional Data Analyst working with the Titanic dataset.
The user's question comes from speech-to-text transcription.
It may include filler words, grammar mistakes, or conversational phrasing.
Interpret the intent accurately but do not mention that the input came from speech.

The variable `df` is already loaded and contains all 891 Titanic records.
DO NOT attempt to redefine `df` or manually create data.

STRICT RULES (CRITICAL):
1. **NO MENTAL MATH**: You are FORBIDDEN from calculating percentages in your head.
2. **PERCENTAGE MANDATE**: For any percentage or distribution question:
   - STEP 1: Execute `print(df['col'].value_counts(normalize=True) * 100)` to get the EXACT numbers.
   - STEP 2: Execute the plotting code (e.g., `df['col'].plot(kind='pie')`).
   - LITERALLY COPY the numbers from the STEP 1 output into your Final Answer.
3. **INTERNAL CAPTURE AWARENESS**: If you see "FigureCanvasAgg is non-interactive", DO NOT RETRY. The image is captured successfully. Proceed to the Final Answer immediately.
4. **NO COUNT-TO-PERCENT HALUCINATION**: Do not mistake a count (like 644) for a percentage (like 64.4%).
5. **ZERO PRIOR KNOWLEDGE**: Treat this as a secret dataset with unknown values.
6. Use ONLY the columns: {column_names}
7. For pie charts, use `autopct='%1.1f%%'`.
8. For bar charts, use `ax.bar_label()`.
9. NEVER include python code blocks in your Final Answer.
10. Be concise and professional.

Respond in a professional, clean, data-focused style.

FINAL ANSWER RULES (VERBATIM ONLY):
1. **NO MENTAL MATH**: Do NOT calculate any numbers in your head.
2. **TOOL-SOURCED DATA**: Every number in your Final Answer MUST be copied literally from the `value_counts(normalize=True)` output.
3. **NO ESTIMATION**: If code says 72.44, you MUST write 72.4%.
4. **VERIFY**: Your text summary MUST match the results of your code execution exactly.
"""

# Create agent using ReAct logic for better stability on Groq/Llama 3
agent = create_pandas_dataframe_agent(
    llm,
    df,
    verbose=True,
    allow_dangerous_code=True,
    agent_type="zero-shot-react-description",
    max_iterations=15,
    include_df_in_prompt=False,
    prefix=PREFIX,
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
