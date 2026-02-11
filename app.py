import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="Survey Dashboard", layout="wide")

QUESTION_COLS = ["Question #1", "Question #2", "Question #3", "Question #4"]

@st.cache_data
def load_data(path: str = "test_data.csv") -> pd.DataFrame:
    df = pd.read_csv(path)
    # Participant average across all questions
    df["Avg Score"] = df[QUESTION_COLS].mean(axis=1)
    return df

df = load_data()

st.title("Survey Dashboard")

# -------------------------
# Sidebar filters (global)
# -------------------------
st.sidebar.header("Filters")
gender_filter = st.sidebar.multiselect(
    "Gender",
    options=sorted(df["Gender"].dropna().unique()),
    default=sorted(df["Gender"].dropna().unique())
)
age_filter = st.sidebar.multiselect(
    "Age",
    options=sorted(df["Age"].dropna().unique()),
    default=sorted(df["Age"].dropna().unique())
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
c3.metric(
    "Highest participant Avg Score",
    f"{best_row['Avg Score']:.2f}",
    help=f"Highest participant average across Question #1–#4 within the filtered data (Participant {best_row['Participant']})."
)
c4.metric(
    "Lowest participant Avg Score",
    f"{worst_row['Avg Score']:.2f}",
    help=f"Lowest participant average across Question #1–#4 within the filtered data (Participant {worst_row['Participant']})."
)

st.caption(
    f"Highest Avg Score: Participant {best_row['Participant']} ({best_row['Gender']}, {best_row['Age']}) • "
    f"Lowest Avg Score: Participant {worst_row['Participant']} ({worst_row['Gender']}, {worst_row['Age']})."
)

# -------------------------
# Horizontal boxplots (side-by-side within each question)
# -------------------------
st.markdown("**Score Distribution (Boxplots)**")

group_by = st.radio(
    "Compare distributions by",
    options=["None", "Gender", "Age"],
    horizontal=True
)

long_df = filtered.melt(
    id_vars=["Participant", "Gender", "Age"],
    value_vars=QUESTION_COLS,
    var_name="Question",
    value_name="Score"
)

if group_by == "None":
    chart = (
        alt.Chart(long_df)
        .mark_boxplot()
        .encode(
            x=alt.X("Score:Q", scale=alt.Scale(domain=[0, 7]), title="Score"),
            y=alt.Y("Question:N", title=""),
            tooltip=["Question", "Score", "Participant", "Gender", "Age"]
        )
        .properties(height=260)
    )
    st.altair_chart(chart, use_container_width=True)

elif group_by == "Gender":
    chart = (
        alt.Chart(long_df)
        .mark_boxplot()
        .encode(
            x=alt.X("Score:Q", scale=alt.Scale(domain=[0, 7]), title="Score"),
            y=alt.Y("Question:N", title=""),
            # KEY: for horizontal boxplots, use yOffset to put M/F side-by-side within each question
            yOffset=alt.YOffset("Gender:N"),
            color=alt.Color(
                "Gender:N",
                scale=alt.Scale(domain=["M", "F"], range=["#3B82F6", "#EC4899"]),  # blue, pink
                legend=alt.Legend(title="Gender")
            ),
            tooltip=["Question", "Gender", "Score", "Participant", "Age"]
        )
        .properties(height=300)
    )
    st.altair_chart(chart, use_container_width=True)

else:  # group_by == "Age"
    chart = (
        alt.Chart(long_df)
        .mark_boxplot()
        .encode(
            x=alt.X("Score:Q", scale=alt.Scale(domain=[0, 7]), title="Score"),
            y=alt.Y("Question:N", title=""),
            yOffset=alt.YOffset("Age:N"),
            color=alt.Color("Age:N", legend=alt.Legend(title="Age Group")),
            tooltip=["Question", "Age", "Score", "Participant", "Gender"]
        )
        .properties(height=320)
    )
    st.altair_chart(chart, use_container_width=True)

st.divider()


# -------------------------
# Tabs
# -------------------------
tab1, tab2 = st.tabs(["Participant View", "Question View"])

# -------------------------
# Tab 1: Participant View
# -------------------------
with tab1:
    st.subheader("Participant View")

    participant = st.selectbox(
        "Select a participant",
        options=sorted(filtered["Participant"].unique())
    )

    p = filtered[filtered["Participant"] == participant].iloc[0]

    left, right = st.columns([1, 2])

    with left:
        st.markdown("**Participant Info**")
        st.write(f"**Participant:** {p['Participant']}")
        st.write(f"**Gender:** {p['Gender']}")
        st.write(f"**Age:** {p['Age']}")
        st.write(f"**Avg Score:** {p['Avg Score']:.2f}")

        st.markdown("**Raw Scores**")
        score_table = pd.DataFrame({
            "Question": QUESTION_COLS,
            "Score": [p[q] for q in QUESTION_COLS]
        })
        st.dataframe(score_table, hide_index=True, use_container_width=True)

    with right:
        # Compare participant scores vs overall mean
        overall_means = filtered[QUESTION_COLS].mean().reset_index()
        overall_means.columns = ["Question", "Overall Mean"]

        participant_scores = pd.DataFrame({
            "Question": QUESTION_COLS,
            "Participant Score": [p[q] for q in QUESTION_COLS]
        })

        comp = overall_means.merge(participant_scores, on="Question")
        comp_long = comp.melt("Question", var_name="Series", value_name="Score")

        chart = (
            alt.Chart(comp_long)
            .mark_bar()
            .encode(
                x=alt.X("Question:N", title=""),
                y=alt.Y("Score:Q", scale=alt.Scale(domain=[0, 7])),
                color="Series:N",
                tooltip=["Question", "Series", "Score"]
            )
            .properties(height=300)
        )

        st.markdown("**Participant vs Overall Mean**")
        st.altair_chart(chart, use_container_width=True)

    st.markdown("**Where do they rank (Avg Score)?**")
    ranking = (
        filtered[["Participant", "Avg Score", "Gender", "Age"]]
        .sort_values("Avg Score", ascending=False)
        .reset_index(drop=True)
    )
    ranking["Rank"] = ranking.index + 1
    st.dataframe(ranking[["Rank", "Participant", "Avg Score", "Gender", "Age"]], use_container_width=True)

# -------------------------
# Tab 2: Question View
# -------------------------
with tab2:
    st.subheader("Question View")

    q = st.selectbox("Select a question", options=QUESTION_COLS)

    q_df = filtered[["Participant", "Gender", "Age", q]].rename(columns={q: "Score"})

    c1, c2, c3 = st.columns(3)
    c1.metric("Mean", f"{q_df['Score'].mean():.2f}")
    c2.metric("Median", f"{q_df['Score'].median():.2f}")
    c3.metric("Std Dev", f"{q_df['Score'].std():.2f}")

    # Distribution histogram
    hist = (
        alt.Chart(q_df)
        .mark_bar()
        .encode(
            x=alt.X("Score:Q", bin=alt.Bin(step=1), title="Score"),
            y=alt.Y("count():Q", title="Count"),
            tooltip=["count()"]
        )
        .properties(height=250)
    )

    # Boxplot by gender
    box_gender = (
        alt.Chart(q_df)
        .mark_boxplot()
        .encode(
            x=alt.X("Gender:N", title="Gender"),
            y=alt.Y("Score:Q", scale=alt.Scale(domain=[0, 7]), title="Score"),
            tooltip=["Gender", "Score"]
        )
        .properties(height=250)
    )

    left, right = st.columns(2)
    with left:
        st.markdown("**Distribution**")
        st.altair_chart(hist, use_container_width=True)
    with right:
        st.markdown("**By Gender**")
        st.altair_chart(box_gender, use_container_width=True)

    # Table: top/bottom participants for that question
    st.markdown("**Top / Bottom Participants**")
    top = q_df.sort_values("Score", ascending=False).head(5)
    bottom = q_df.sort_values("Score", ascending=True).head(5)

    t1, t2 = st.columns(2)
    with t1:
        st.markdown("Top 5")
        st.dataframe(top, use_container_width=True, hide_index=True)
    with t2:
        st.markdown("Bottom 5")
        st.dataframe(bottom, use_container_width=True, hide_index=True)

    # Breakdown by age
    st.markdown("**Average by Age Group**")
    age_means = q_df.groupby("Age")["Score"].mean().reset_index().rename(columns={"Score": "Mean Score"})
    age_chart = (
        alt.Chart(age_means)
        .mark_bar()
        .encode(
            x=alt.X("Age:N", title="Age Group"),
            y=alt.Y("Mean Score:Q", title="Mean Score", scale=alt.Scale(domain=[0, 7])),
            tooltip=["Age", "Mean Score"]
        )
        .properties(height=250)
    )
    st.altair_chart(age_chart, use_container_width=True)

st.divider()

# -------------------------
# Data viewer + download
# -------------------------
st.subheader("Data")

view_option = st.selectbox(
    "Choose what to view",
    options=["Filtered data (current view)", "Full data (all rows)"]
)

data_to_show = filtered if view_option.startswith("Filtered") else df

with st.expander("View dataset"):
    st.dataframe(data_to_show, use_container_width=True)

csv_bytes = data_to_show.to_csv(index=False).encode("utf-8")
st.download_button(
    label="Download CSV",
    data=csv_bytes,
    file_name="survey_data.csv",
    mime="text/csv"
)
