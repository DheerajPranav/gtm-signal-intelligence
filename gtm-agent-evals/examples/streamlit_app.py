"""Streamlit app demonstrating gtm-agent-evals rubrics as reusable evaluators.

Run: streamlit run examples/streamlit_app.py
"""

import streamlit as st
from gtm_agent_evals import ICPRubric, EmailRubric, PersonaRubric, CritiqueRubric, Seniority


st.set_page_config(page_title="GTM Agent Evals", layout="wide")

st.title("🔍 GTM Agent Evals Rubric Viewer")
st.write("Interactive explorer for framework-agnostic evaluation rubrics.")

# Sidebar navigation
rubric = st.sidebar.selectbox(
    "Select Rubric",
    ["ICP Scoring", "Email Quality", "Persona Validation", "Critique Guidelines"],
)

# --- ICP Scoring Rubric ---
if rubric == "ICP Scoring":
    st.header("ICP Scoring Rubric")
    st.markdown(
        "**Purpose:** Evaluate company fit across 4 dimensions with behavioral signal dominance."
    )

    st.subheader("Dimensions & Weights")
    cols = st.columns(2)
    with cols[0]:
        st.metric("Behavioral", f"{ICPRubric.WEIGHTS['behavioral']:.0%}")
        st.caption(ICPRubric.DIMENSION_DESCRIPTIONS["behavioral"])

    with cols[1]:
        st.metric("Firmographic", f"{ICPRubric.WEIGHTS['firmographic']:.0%}")
        st.caption(ICPRubric.DIMENSION_DESCRIPTIONS["firmographic"])

    cols = st.columns(2)
    with cols[0]:
        st.metric("Timing", f"{ICPRubric.WEIGHTS['timing']:.0%}")
        st.caption(ICPRubric.DIMENSION_DESCRIPTIONS["timing"])

    with cols[1]:
        st.metric("Technographic", f"{ICPRubric.WEIGHTS['technographic']:.0%}")
        st.caption(ICPRubric.DIMENSION_DESCRIPTIONS["technographic"])

    st.subheader("Try It")
    col1, col2 = st.columns(2)
    with col1:
        firm = st.slider("Firmographic (0-10)", 0, 10, 5)
        tech = st.slider("Technographic (0-10)", 0, 10, 5)

    with col2:
        behav = st.slider("Behavioral (0-10)", 0, 10, 5)
        timing = st.slider("Timing (0-10)", 0, 10, 5)

    dimensions = {
        "firmographic": float(firm),
        "technographic": float(tech),
        "behavioral": float(behav),
        "timing": float(timing),
    }
    score = ICPRubric.compute_overall_score(dimensions)

    st.metric("Overall Score", f"{score:.2f} / 10.0")
    st.write(f"**Pass Threshold:** 6.5 → {('✅ PASS' if score >= 6.5 else '❌ FAIL')}")

# --- Email Quality Rubric ---
elif rubric == "Email Quality":
    st.header("Email Quality Rubric")
    st.markdown(
        "**Purpose:** Score cold email quality across 5 dimensions. Would-send gate requires all thresholds met."
    )

    # Display scoring guides
    st.subheader("Scoring Guides")
    for dim in ["personalization", "relevance", "cta", "spam_risk"]:
        with st.expander(f"{dim.title()} (0-5 scale)", expanded=False):
            guide = EmailRubric.DIMENSIONS[dim]["scoring"]
            for score, desc in sorted(guide.items(), reverse=True):
                st.write(f"**{score}:** {desc}")

    # Try it
    st.subheader("Try It")
    col1, col2 = st.columns(2)
    with col1:
        pers = st.slider("Personalization", 0, 5, 3)
        rel = st.slider("Relevance", 0, 5, 3)

    with col2:
        cta = st.slider("CTA", 0, 5, 3)
        spam = st.slider("Spam Risk (lower=better)", 0, 5, 2)

    criteria = EmailRubric.DIMENSIONS["would_send"]["pass_criteria"]

    # Check thresholds
    checks = {
        "Personalization": (float(pers), criteria["personalization"], ">="),
        "Relevance": (float(rel), criteria["relevance"], ">="),
        "CTA": (float(cta), criteria["cta"], ">="),
        "Spam Risk": (float(spam), criteria["spam_risk"], "<="),
    }

    would_send = all(
        (val >= thresh if op == ">=" else val <= thresh)
        for val, thresh, op in checks.values()
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Would Send", "✅ YES" if would_send else "❌ NO")

    with col2:
        st.write("**Thresholds:**")
        for name, (val, thresh, op) in checks.items():
            status = "✅" if (val >= thresh if op == ">=" else val <= thresh) else "❌"
            st.write(f"{status} {name}: {val} {op} {thresh}")

# --- Persona Validation Rubric ---
elif rubric == "Persona Validation":
    st.header("Persona Validation Rubric")
    st.markdown(
        "**Purpose:** Validate buyer persona completeness and grounding."
    )

    st.subheader("Required Fields")
    for field, desc in PersonaRubric.REQUIRED_FIELDS.items():
        st.write(f"- **{field}**: {desc}")

    st.subheader("Grounding Terms by Segment")
    segment = st.selectbox(
        "Select segment",
        list(PersonaRubric.GROUNDING_TERMS.keys()),
    )
    terms = PersonaRubric.GROUNDING_TERMS[segment]
    st.write(f"**{segment.title()}:** {', '.join(terms)}")

    st.subheader("Try It")
    persona_data = {}

    col1, col2 = st.columns(2)
    with col1:
        persona_data["title"] = st.text_input("Title", "VP Revenue Operations")
        persona_data["department"] = st.text_input("Department", "RevOps")
        persona_data["seniority"] = st.selectbox(
            "Seniority",
            [s.value for s in Seniority],
        )

    with col2:
        persona_data["pain_points"] = st.text_area(
            "Pain Points (comma-separated)",
            "forecast accuracy, pipeline visibility",
        ).split(",")
        persona_data["priorities"] = st.text_area(
            "Priorities (comma-separated)",
            "ROI tracking, cycle time",
        ).split(",")
        persona_data["objections"] = st.text_area(
            "Objections (comma-separated)",
            "cost, implementation",
        ).split(",")

    persona_data["buying_influence"] = st.selectbox(
        "Buying Influence", ["high", "medium", "low"]
    )

    is_complete = PersonaRubric.is_complete(persona_data)
    st.metric("Complete", "✅ YES" if is_complete else "❌ NO")

    if not is_complete:
        missing = [
            f
            for f in PersonaRubric.REQUIRED_FIELDS
            if f not in persona_data or not persona_data[f]
        ]
        st.warning(f"Missing fields: {', '.join(missing)}")

# --- Critique Guidelines ---
elif rubric == "Critique Guidelines":
    st.header("Critique Rubric")
    st.markdown(
        "**Purpose:** Skeptical email review using LLM judge. Would-send gate with strict thresholds."
    )

    st.subheader("System Prompt")
    st.code(CritiqueRubric.SYSTEM_PROMPT, language="text")

    st.subheader("Would-Send Thresholds")
    for dim, threshold in CritiqueRubric.SHOULD_SEND_THRESHOLDS.items():
        direction = "≤" if dim == "spam_risk" else "≥"
        st.write(f"- {dim}: {direction} {threshold}")

    st.info(
        "💡 Thresholds must ALL be met for would_send=true. Bias toward 'no' rather than 'yes'."
    )

st.sidebar.divider()
st.sidebar.markdown(
    """
**Learn More:**
- [GitHub](https://github.com/DheerajPranav/gtm-signal-intelligence/tree/main/gtm-agent-evals)
- [README](https://github.com/DheerajPranav/gtm-signal-intelligence/tree/main/gtm-agent-evals/README.md)

**About:**
Open-source evals kit extracted from production GTM AI agents.
Framework-agnostic — use anywhere.
"""
)
