import streamlit as st
import google.generativeai as genai
import textwrap
import os # Import os for file path handling

# --- Streamlit App Setup ---
st.title("WSDC Debate Assistant")

# --- API Key Handling (Placeholder for now) ---
# Use st.secrets for secure API key handling in Streamlit Cloud
# The actual key should be in a secrets.toml file in the .streamlit directory
try:
    GEMINI_API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
except KeyError:
    st.error("GEMINI_API_KEY not found in Streamlit secrets. Please add it.")
    model = None # Ensure model is None if key is missing
except Exception as e:
    st.error(f"Error configuring Gemini API: {e}")
    model = None


# --- Knowledge Base Loading with Caching ---
@st.cache_data # Cache the knowledge base to avoid reloading
def load_knowledge_base(file_path="distilled_knowledge.txt"):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            knowledge = f.read()
        st.success("✅ Distilled knowledge loaded successfully.")
        return knowledge
    except FileNotFoundError:
        st.error(f"🚨 ERROR: `{file_path}` not found! Please upload it.")
        return None
    except Exception as e:
        st.error(f"Error loading knowledge base: {e}")
        return None

distilled_knowledge = load_knowledge_base()


# --- Helper function for formatted output (adapted for Streamlit Markdown) ---
def to_markdown(text):
  text = text.replace('•', '  *')
  return text # Return text for Streamlit, not Markdown object

# --- Extracted Core Logic Functions ---

# Function from BLOCK 3: The Master Speech Drafter
def draft_master_speech(motion, side, speaker_role, knowledge_base, model):
    if not knowledge_base or not model:
        st.error("Knowledge base not loaded or model not initialized.")
        return None

    role_instructions = ""
    if speaker_role.lower() == "1st proposition":
        role_instructions = "As 1st Prop, you set up the debate. Your speech needs a clear intro, definitions, team line, speaker split, and then you must fully develop the first argument(s)."
    elif speaker_role.lower() == "2nd opposition":
        role_instructions = "As 2nd Opp, your job is to clash. Start with direct rebuttal, then introduce your team's remaining substantive arguments."
    elif speaker_role.lower() == "3rd speaker":
        role_instructions = "As 3rd Speaker, your role is to crystalize the debate. Identify the key clash points and explain why your team won them. No new arguments."

    prompt = f"""
    You are an expert WSDC Head Coach and speechwriter, using only the "Synthesized Knowledge Briefing" provided.

    --- SYNTHESIZED KNOWLEDGE BRIEFING START ---
    {knowledge_base}
    --- SYNTHESIZED KNOWLEDGE BRIEFING END ---

    DEBATE DETAILS:
    - Motion: "{motion}"
    - My Team's Side: {side}
    - My Speaker Role: {speaker_role}

    Your task is a two-part process:

    ### PART 1: ESTABLISH THE CASE FOUNDATION
    First, you must create the foundational elements of our case. This section should be detailed, well-explained, and principled, like in the V2 style.
    - **Detailed Definition:** Provide a strategic and nuanced definition of the key terms in the motion. Explain the reasoning behind your definition.
    - **Detailed Team Line / Counter-Stance:** Provide a comprehensive and memorable Team Line (for Prop) or Counter-Stance (for Opp). Explain the core philosophy it represents.

    ### PART 2: DRAFT THE SPEAKER-SPECIFIC SPEECH
    Now, using the foundation you just established in Part 1, draft a concise speech outline for the specified speaker role.
    - **Follow Role Responsibilities:** Adhere strictly to the specific responsibilities for a {speaker_role}. Be very crisp.
    - **Integrate the Foundation:** Your speech should clearly reflect the Definition and Team Line from Part 1.
    - **Use Evidence:** Incorporate concepts and quotes from the knowledge briefing.
    - **Structure Clearly:** Use markdown for headings and bullet points.

    SPECIFIC ROLE RESPONSIBILITIES:
    {role_instructions}

    Now, generate the complete output, starting with Part 1.
    """
    try:
        with st.spinner("Drafting Master Speech..."):
            response = model.generate_content(prompt)
            return response.text
    except Exception as e:
        st.error(f"Error generating master speech: {e}")
        return None


# Function from BLOCK 1: The Crisp Case Construction Agent
def generate_wsdc_case_crisp(motion, side, knowledge_base, model):
    if not knowledge_base or not model:
        st.error("Knowledge base not loaded or model not initialized.")
        return None
    side_specific_instructions = ""
    if side.lower() == "proposition":
        persona = "You are an elite WSDC Head Coach known for your no-nonsense, direct, and efficient style. You create powerfully simple cases."
        side_specific_instructions = "**STRATEGIC GOAL FOR PROPOSITION:** Build a compelling, principled case FOR the motion."
    elif side.lower() == "opposition":
        persona = "You are an elite WSDC Head Coach known for your sharp, concise, and devastatingly clear Opposition strategies."
        side_specific_instructions = "**CRITICAL INSTRUCTIONS FOR OPPOSITION:** Dismantle the philosophy behind the motion using first principles. Do NOT generate arguments that sound like weak proposition points."
    prompt = f"""{persona} Your sole source of information is the "Synthesized Knowledge Briefing" provided below.
--- SYNTHESIZED KNOWLEDGE BRIEFING START ---
{knowledge_base}
--- SYNTHESIZED KNOWLEDGE BRIEFING END ---
DEBATE DETAILS:
- Motion: "{motion}"
- My Team's Side: {side}
{side_specific_instructions}
--- OUTPUT FORMATTING RULES (VERY IMPORTANT) ---
- **Brevity is Key:** Use bullet points. Be Direct. Format as a Cheat Sheet.
--- EXAMPLE OF THE DESIRED CRISP STYLE ---
**Argument 2: The Argument from Economic Inevitability**
*   **Core Logic (1 sentence):** Global economic integration makes isolationism an impossible and self-defeating strategy.
*   **Mechanism (Bullets):** - Supply chains are interconnected. - Prosperity depends on trade.
*   **Impact (1 sentence):** The motion is the only realistic path to prosperity.
*   **Evidence:** [Cite a relevant quote or concept]
--- END OF EXAMPLE ---
Now, generate the full case outline following these strict formatting rules.
CASE OUTLINE REQUIREMENTS:
1.  **Definition (1-2 sentences max):**
2.  **Team Line / Counter-Stance (1 sentence max)::**
3.  **Arguments (Follow the crisp example style):** Develop three distinct arguments.
"""
    try:
        with st.spinner(f"Generating CRISP Case for side '{side}'..."):
            response = model.generate_content(prompt)
            return response.text
    except Exception as e:
        st.error(f"Error generating crisp case: {e}")
        return None


# Function from BLOCK 2: The Rebuttal Sparring Partner
def generate_rebuttals(motion, opponent_arg, knowledge_base, model):
    if not knowledge_base or not model:
        st.error("Knowledge base not loaded or model not initialized.")
        return None
    prompt = f"""
    You are a sharp and analytical WSDC debater, an expert in refutation. Your worldview is shaped by the "Synthesized Knowledge Briefing" below.

    The debate motion is: "{motion}"

    An opponent has just made the following argument. Your job is to generate 3 distinct lines of rebuttal against it. For each rebuttal point, clearly state your attack and use evidence from the briefing to support it.

    OPPONENT'S ARGUMENT:
    "{opponent_arg}"
    """
    try:
        with st.spinner("Generating rebuttal points..."):
            response = model.generate_content(prompt)
            return response.text
    except Exception as e:
        st.error(f"Error generating rebuttals: {e}")
        return None

# --- Streamlit App Layout and Logic ---

st.header("Debate Configuration")

CURRENT_MOTION = st.text_input(
    "🎯 Set Your Debate Motion for this Session",
    "This House regrets the commercialization of space exploration."
)

side = st.selectbox(
    "🎤 Select Your Team's Side",
    ["Proposition", "Opposition"]
)

speaker_role = st.selectbox(
    "🗣️ Select Speaker Role (for Master Speech)",
    ["1st Proposition", "2nd Opposition", "3rd Speaker"]
)

opponent_argument = st.text_area(
    "💬 Enter Opponent's Argument to Rebut (for Rebuttal Sparring Partner)",
    "Profit motive helps optimise efficient deployment of limited resource in space exploration."
)

st.header("Generate Debate Content")

if model and distilled_knowledge:
    if st.button("Generate Master Speech"):
        if CURRENT_MOTION.strip():
            speech_draft = draft_master_speech(CURRENT_MOTION, side, speaker_role, distilled_knowledge, model)
            if speech_draft:
                st.subheader(f"📜 Master Speech Draft: {speaker_role} ({side})")
                st.markdown(to_markdown(speech_draft))
        else:
            st.warning("Please enter a debate motion.")

    st.markdown("---") # Separator

    if st.button("Generate Crisp Cases (Prop & Opp)"):
        if CURRENT_MOTION.strip():
            st.subheader("🏛️ Proposition Case")
            prop_case = generate_wsdc_case_crisp(CURRENT_MOTION, "Proposition", distilled_knowledge, model)
            if prop_case:
                st.markdown(to_markdown(prop_case))

            st.subheader("⚔️ Opposition Case")
            opp_case = generate_wsdc_case_crisp(CURRENT_MOTION, "Opposition", distilled_knowledge, model)
            if opp_case:
                 st.markdown(to_markdown(opp_case))
        else:
             st.warning("Please enter a debate motion.")

    st.markdown("---") # Separator

    if st.button("Generate Rebuttals"):
        if CURRENT_MOTION.strip() and opponent_argument.strip():
            rebuttal_points = generate_rebuttals(CURRENT_MOTION, opponent_argument, distilled_knowledge, model)
            if rebuttal_points:
                st.subheader("💬 Rebuttal Points")
                st.markdown(to_markdown(rebuttal_points))
        elif not CURRENT_MOTION.strip():
             st.warning("Please enter a debate motion.")
        else:
            st.warning("Please enter an opponent's argument to rebut.")

elif not model:
    st.error("Gemini API not configured. Please check your API key in Streamlit secrets.")
elif not distilled_knowledge:
    st.error("Knowledge base not loaded. Please ensure 'distilled_knowledge.txt' is in the same directory.")
