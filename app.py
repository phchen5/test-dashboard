# app.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(page_title="Survey Dashboard", layout="wide")

QUESTION_COLS = ["Question #1", "Question #2", "Question #3", "Question #4"]

@st.cache_data
def load_data(path: str = "test_data.csv") -> pd.DataFrame:
    df = pd.read_csv(path)
    df["Avg Score"] = df[QUESTION_COLS].mean(axis=1)
    return df

def to_long(df: pd.DataFrame) -> pd.DataFrame:
    return df.melt(
        id_vars=["Participant", "Gender", "Age", "Avg Score"],
        value_vars=QUESTION_COLS,
        var_name="Question",
        value_name="Score"
    )

# ---- Theme (Seaborn) ----
sns.set_theme(style="ticks")

df = load_data()
st.title("Survey Dashboard")

# -------------------------
# Sidebar filters (global)
# -------------------------
st.sidebar.header("Filters")
gender_filter = st.sidebar.multiselect(
    "Gender",
    options=sorted(df["Gender"].dropna().unique()),
    default=sorted(df["Gender"].dropna().unique()),
)
age_filter = st.sidebar.multiselect(
    "Age",
    options=sorted(df["Age"].dropna().unique()),
    default=sorted(df["Age"].dropna().unique()),
)

filtered = df[df["Gender"].isin(gender_filter) & df["Age"].isin(age_filter)].copy()
if filtered.empty:
    st.warning("No data matches the current filters. Try expanding Gender/Age selections.")
    st.stop()

# -------------------------
# Overview (top part)
# -------------------------
st.subheader("Overview")

best_row = filtered.loc[filtered["Avg Score"].idxmax()]
worst_row = filtered.loc[filtered["Avg Score"].idxmin()]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Participants (filtered)", len(filtered))
c2.metric("Overall mean (Avg Score)", f"{filtered['Avg Score'].mean():.2f}")
c3.metric("Highest participant Avg Score (Q1–Q4)", f"{best_row['Avg Score']:.2f}")
c4.metric("Lowest participant Avg Score (Q1–Q4)", f"{worst_row['Avg Score']:.2f}")

st.caption(
    f"Highest: Participant {best_row['Participant']} ({best_row['Gender']}, {best_row['Age']}) • "
    f"Lowest: Participant {worst_row['Participant']} ({worst_row['Gender']}, {worst_row['Age']})."
)

# -------------------------
# Boxplots (Seaborn)
# -------------------------
st.markdown("**Score Distribution (Boxplots)**")

mode = st.radio(
    "How to compare distributions",
    options=[
        "Overall (no grouping)",
        "Grouped boxplot (hue = Gender)",
        "Side-by-side panels (one plot per Gender)",
        "Side-by-side panels (one plot per Age group)",
    ],
    horizontal=False
)

long_df = to_long(filtered)

# Colors you asked for
gender_palette = {"M": "tab:blue", "F": "tab:pink"}

def draw_overall_boxplot(data_long: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(10, 4))
    sns.boxplot(
        data=data_long,
        x="Question", y="Score",
        ax=ax
    )
    sns.despine(offset=10, trim=True)
    ax.set_xlabel("")
    ax.set_ylabel("Score")
    ax.set_ylim(0, 7)
    fig.tight_layout()
    return fig

def draw_grouped_hue_boxplot(data_long: pd.DataFrame):
    # One chart, grouped by question, hue = gender (nested boxplot)
    fig, ax = plt.subplots(figsize=(10, 4))
    sns.boxplot(
        data=data_long,
        x="Question", y="Score",
        hue="Gender",
        palette=gender_palette,
        ax=ax
    )
    sns.despine(offset=10, trim=True)
    ax.set_xlabel("")
    ax.set_ylabel("Score")
    ax.set_ylim(0, 7)
    ax.legend(title="Gender", loc="upper right")
    fig.tight_layout()
    return fig

def draw_panels_by_gender(data_long: pd.DataFrame):
    # Two equal-size panels: M and F
    genders = [g for g in ["M", "F"] if g in data_long["Gender"].unique()]
    n = len(genders)
    fig, axes = plt.subplots(1, n, figsize=(12, 4), sharey=True, sharex=True)

    if n == 1:
        axes = [axes]

    for ax, g in zip(axes, genders):
        sub = data_long[data_long["Gender"] == g]
        sns.boxplot(
            data=sub,
            x="Question", y="Score",
            color=gender_palette.get(g, None),
            ax=ax
        )
        sns.despine(offset=10, trim=True)
        ax.set_title(f"Gender = {g}")
        ax.set_xlabel("")
        ax.set_ylabel("Score" if ax == axes[0] else "")
        ax.set_ylim(0, 7)

    fig.tight_layout()
    return fig

def draw_panels_by_age(data_long: pd.DataFrame):
    # Panels for each age group (can get wide if many groups)
    ages = sorted(data_long["Age"].dropna().unique())
    n = len(ages)

    # If many age groups, wrap into multiple rows
    cols = min(4, n)
    rows = (n + cols - 1) // cols

    fig, axes = plt.subplots(rows, cols, figsize=(4.2 * cols, 3.6 * rows), sharey=True)
    axes = axes.flatten() if n > 1 else [axes]

    for i, age in enumerate(ages):
        ax = axes[i]
        sub = data_long[data_long["Age"] == age]
        sns.boxplot(
            data=sub,
            x="Question", y="Score",
            ax=ax
        )
        sns.despine(offset=10, trim=True)
        ax.set_title(f"Age = {age}")
        ax.set_xlabel("")
        ax.set_ylabel("Score" if i % cols == 0 else "")
        ax.set_ylim(0, 7)

    # Hide unused axes
    for j in range(n, len(axes)):
        axes[j].axis("off")

    fig.tight_layout()
    return fig

if mode == "Overall (no grouping)":
    st.pyplot(draw_overall_boxplot(long_df))

elif mode == "Grouped boxplot (hue = Gender)":
    st.pyplot(draw_grouped_hue_boxplot(long_df))

elif mode == "Side-by-side panels (one plot per Gender)":
    st.pyplot(draw_panels_by_gender(long_df))

else:  # panels by age
    st.pyplot(draw_panels_by_age(long_df))

st.divider()

# -------------------------
# Tabs
# -------------------------
tab1, tab2 = st.tabs(["Participant View", "Question View"])

with tab1:
    st.subheader("Participant View")
    participant = st.selectbox("Select a participant", options=sorted(filtered["Participant"].unique()))
    p = filtered[filtered["Participant"] == participant].iloc[0]

    left, right = st.columns([1, 2])

    with left:
        st.markdown("**Participant Info**")
        st.write(f"**Participant:** {p['Participant']}")
        st.write(f"**Gender:** {p['Gender']}")
        st.write(f"**Age:** {p['Age']}")
        st.write(f"**Avg Score (Q1–Q4):** {p['Avg Score']:.2f}")

        st.markdown("**Raw Scores**")
        st.dataframe(
            pd.DataFrame({"Question": QUESTION_COLS, "Score": [p[q] for q in QUESTION_COLS]}),
            hide_index=True,
            use_container_width=True
        )

    with right:
        st.markdown("**Participant vs Overall Mean (by question)**")
        comp = pd.DataFrame({
            "Question": QUESTION_COLS,
            "Participant": [p[q] for q in QUESTION_COLS],
            "Overall Mean": [filtered[q].mean() for q in QUESTION_COLS],
        })
        comp_long = comp.melt("Question", var_name="Series", value_name="Score")

        fig, ax = plt.subplots(figsize=(10, 3.5))
        sns.barplot(data=comp_long, x="Question", y="Score", hue="Series", ax=ax)
        sns.despine(offset=10, trim=True)
        ax.set_ylim(0, 7)
        ax.set_xlabel("")
        ax.set_ylabel("Score")
        ax.legend(title="")
        fig.tight_layout()
        st.pyplot(fig)

    st.markdown("**Ranking (Avg Score across Q1–Q4)**")
    ranking = (
        filtered[["Participant", "Avg Score", "Gender", "Age"]]
        .sort_values("Avg Score", ascending=False)
        .reset_index(drop=True)
    )
    ranking["Rank"] = ranking.index + 1
    st.dataframe(ranking[["Rank", "Participant", "Avg Score", "Gender", "Age"]], use_container_width=True)

with tab2:
    st.subheader("Question View")
    q = st.selectbox("Select a question", options=QUESTION_COLS)

    q_df = filtered[["Participant", "Gender", "Age", q]].rename(columns={q: "Score"})

    c1, c2, c3 = st.columns(3)
    c1.metric("Mean", f"{q_df['Score'].mean():.2f}")
    c2.metric("Median", f"{q_df['Score'].median():.2f}")
    c3.metric("Std Dev", f"{q_df['Score'].std():.2f}" if len(q_df) > 1 else "—")

    left, right = st.columns(2)

    with left:
        st.markdown("**Distribution (histogram)**")
        fig, ax = plt.subplots(figsize=(6, 3.5))
        sns.histplot(data=q_df, x="Score", bins=range(0, 9), ax=ax)
        sns.despine(offset=10, trim=True)
        ax.set_xlabel("Score")
        ax.set_ylabel("Count")
        fig.tight_layout()
        st.pyplot(fig)

    with right:
        st.markdown("**By Gender (boxplot)**")
        fig, ax = plt.subplots(figsize=(6, 3.5))
        sns.boxplot(data=q_df, x="Gender", y="Score", palette=gender_palette, ax=ax)
        sns.despine(offset=10, trim=True)
        ax.set_ylim(0, 7)
        ax.set_xlabel("Gender")
        ax.set_ylabel("Score")
        fig.tight_layout()
        st.pyplot(fig)

    st.markdown("**Top / Bottom Participants**")
    top = q_df.sort_values("Score", ascending=False).head(5)
    bottom = q_df.sort_values("Score", ascending=True).head(5)
    t1, t2 = st.columns(2)
    with t1:
        st.markdown("Top 5")
        st.dataframe(top, hide_index=True, use_container_width=True)
    with t2:
        st.markdown("Bottom 5")
        st.dataframe(bottom, hide_index=True, use_container_width=True)

st.divider()

# -------------------------
# Data viewer + download
# -------------------------
st.subheader("Data")

view_option = st.selectbox("Choose what to view", ["Filtered data (current view)", "Full data (all rows)"])
data_to_show = filtered if view_option.startswith("Filtered") else df

with st.expander("View dataset"):
    st.dataframe(data_to_show, use_container_width=True)

st.download_button(
    "Download CSV",
    data=data_to_show.to_csv(index=False).encode("utf-8"),
    file_name="survey_data.csv",
    mime="text/csv"
)
