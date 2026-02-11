# app.py (Plotly version with Plotly tabs)
import streamlit as st
import pandas as pd
import plotly.express as px

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

long_df = to_long(filtered)

# Orders + colors
question_order = QUESTION_COLS
age_order = sorted(filtered["Age"].dropna().unique())
gender_color = {"M": "#3B82F6", "F": "#EC4899"}

# -------------------------
# Overview
# -------------------------
st.subheader("Overview")

best_row = filtered.loc[filtered["Avg Score"].idxmax()]
worst_row = filtered.loc[filtered["Avg Score"].idxmin()]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Participants (filtered)", len(filtered))
c2.metric("Overall mean (Avg Score)", f"{filtered['Avg Score'].mean():.2f}")
c3.metric(
    "Highest Avg Score (participant)",
    f"{best_row['Avg Score']:.2f}",
    help=f"Highest participant average across Q1–Q4 in the filtered data: {best_row['Participant']}."
)
c4.metric(
    "Lowest Avg Score (participant)",
    f"{worst_row['Avg Score']:.2f}",
    help=f"Lowest participant average across Q1–Q4 in the filtered data: {worst_row['Participant']}."
)

st.caption(
    f"Highest: {best_row['Participant']} ({best_row['Gender']}, {best_row['Age']}) • "
    f"Lowest: {worst_row['Participant']} ({worst_row['Gender']}, {worst_row['Age']})."
)

st.divider()

# -------------------------
# Participant Distribution (Plotly)
# -------------------------
st.markdown("### Participant Distribution")

gender_counts = filtered["Gender"].value_counts().reset_index()
gender_counts.columns = ["Gender", "Count"]

age_counts = (
    filtered["Age"]
    .value_counts()
    .reindex(age_order)
    .fillna(0)
    .astype(int)
    .reset_index()
)
age_counts.columns = ["Age", "Count"]

colL, colR = st.columns(2)

with colL:
    fig_gender = px.bar(
        gender_counts,
        x="Gender",
        y="Count",
        text="Count",
        template="plotly_dark",
        title="Gender",
    )
    fig_gender.update_traces(
        marker_color=[gender_color.get(g, "#999999") for g in gender_counts["Gender"]],
        textposition="outside",
        cliponaxis=False,
    )
    fig_gender.update_layout(
        margin=dict(l=20, r=20, t=50, b=20),
        xaxis_title="",
        yaxis_title="Count",
    )
    fig_gender.update_yaxes(dtick=1)
    st.plotly_chart(fig_gender, use_container_width=True)

with colR:
    fig_age = px.bar(
        age_counts,
        x="Age",
        y="Count",
        text="Count",
        template="plotly_dark",
        title="Age Group",
        category_orders={"Age": age_order},
    )
    fig_age.update_traces(textposition="outside", cliponaxis=False)
    fig_age.update_layout(
        margin=dict(l=20, r=20, t=50, b=20),
        xaxis_title="",
        yaxis_title="Count",
        xaxis_tickangle=-25,
    )
    fig_age.update_yaxes(dtick=1)
    st.plotly_chart(fig_age, use_container_width=True)

st.divider()

# -------------------------
# Score Distribution (Boxplots) (Plotly)
# -------------------------
st.markdown("### Score Distribution")

split_by = st.selectbox("Split distribution by", ["None", "Gender", "Age"], index=0)

if split_by == "None":
    fig_box = px.box(
        long_df,
        x="Question",
        y="Score",
        points="all",
        template="plotly_dark",
        category_orders={"Question": question_order},
        title="Boxplots by Question",
    )
    fig_box.update_layout(margin=dict(l=20, r=20, t=60, b=20), xaxis_title="", yaxis_title="Score")
else:
    hue_col = "Gender" if split_by == "Gender" else "Age"
    fig_box = px.box(
        long_df,
        x="Question",
        y="Score",
        color=hue_col,
        points="all",
        template="plotly_dark",
        category_orders={"Question": question_order, "Age": age_order},
        color_discrete_map=gender_color if hue_col == "Gender" else None,
        title=f"Boxplots by Question (split by {hue_col})",
    )
    fig_box.update_layout(
        legend=dict(title=hue_col, x=1.02, y=1.0, xanchor="left", yanchor="top"),
        margin=dict(l=20, r=180, t=60, b=20),
        xaxis_title="",
        yaxis_title="Score",
    )

fig_box.update_yaxes(range=[0, 7], dtick=1)
st.plotly_chart(fig_box, use_container_width=True)

st.divider()

# -------------------------
# Tabs (Plotly)
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

        score_table = pd.DataFrame({"Question": QUESTION_COLS, "Score": [p[q] for q in QUESTION_COLS]})
        st.dataframe(score_table, hide_index=True, use_container_width=True)

    with right:
        st.markdown("**Participant vs Overall Mean (by question)**")

        comp = pd.DataFrame({
            "Question": QUESTION_COLS,
            "Participant": [p[q] for q in QUESTION_COLS],
            "Overall Mean": [filtered[q].mean() for q in QUESTION_COLS],
        })

        comp_long = comp.melt("Question", var_name="Series", value_name="Score")

        fig_comp = px.bar(
            comp_long,
            x="Question",
            y="Score",
            color="Series",
            barmode="group",
            template="plotly_dark",
            category_orders={"Question": question_order},
            title="",
        )
        fig_comp.update_layout(margin=dict(l=20, r=20, t=20, b=20), xaxis_title="", yaxis_title="Score")
        fig_comp.update_yaxes(range=[0, 7], dtick=1)
        st.plotly_chart(fig_comp, use_container_width=True)

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
        fig_hist = px.histogram(
            q_df,
            x="Score",
            nbins=7,
            template="plotly_dark",
            title="",
        )
        fig_hist.update_layout(margin=dict(l=20, r=20, t=20, b=20), xaxis_title="Score", yaxis_title="Count")
        fig_hist.update_xaxes(dtick=1)
        fig_hist.update_yaxes(dtick=1)
        st.plotly_chart(fig_hist, use_container_width=True)

    with right:
        st.markdown("**By Gender (boxplot)**")
        fig_q_gender = px.box(
            q_df,
            x="Gender",
            y="Score",
            points="all",
            template="plotly_dark",
            color="Gender",
            color_discrete_map=gender_color,
            title="",
        )
        fig_q_gender.update_layout(margin=dict(l=20, r=20, t=20, b=20), xaxis_title="Gender", yaxis_title="Score", showlegend=False)
        fig_q_gender.update_yaxes(range=[0, 7], dtick=1)
        st.plotly_chart(fig_q_gender, use_container_width=True)

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

    st.markdown("**Average by Age Group**")
    age_means = q_df.groupby("Age")["Score"].mean().reindex(age_order).reset_index()
    age_means.columns = ["Age", "Mean Score"]

    fig_age_mean = px.bar(
        age_means,
        x="Age",
        y="Mean Score",
        template="plotly_dark",
        category_orders={"Age": age_order},
        title="",
        text="Mean Score",
    )
    fig_age_mean.update_traces(texttemplate="%{text:.2f}", textposition="outside", cliponaxis=False)
    fig_age_mean.update_layout(margin=dict(l=20, r=20, t=20, b=20), xaxis_title="Age Group", yaxis_title="Mean Score", xaxis_tickangle=-25)
    fig_age_mean.update_yaxes(range=[0, 7], dtick=1)
    st.plotly_chart(fig_age_mean, use_container_width=True)

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
