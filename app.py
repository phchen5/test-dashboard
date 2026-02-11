import streamlit as st
import pandas as pd

st.set_page_config(page_title="Survey Dashboard", layout="wide")
st.title("Survey Dashboard (Test Data)")

# Load data
@st.cache_data
def load_data(path="test_data.csv"):
    df = pd.read_csv(path)
    return df

df = load_data()

# Basic cleanup / computed columns
question_cols = ["Question #1", "Question #2", "Question #3", "Question #4"]
df["Avg Score"] = df[question_cols].mean(axis=1)

# Sidebar filters
st.sidebar.header("Filters")
gender_filter = st.sidebar.multiselect("Gender", sorted(df["Gender"].unique()), default=sorted(df["Gender"].unique()))
age_filter = st.sidebar.multiselect("Age", sorted(df["Age"].unique()), default=sorted(df["Age"].unique()))

filtered = df[df["Gender"].isin(gender_filter) & df["Age"].isin(age_filter)].copy()

# Show data
st.subheader("Data Preview")
st.dataframe(filtered, use_container_width=True)

# Summary metrics
st.subheader("Summary")
col1, col2, col3 = st.columns(3)
col1.metric("Participants", len(filtered))
col2.metric("Overall Avg Score", f"{filtered['Avg Score'].mean():.2f}" if len(filtered) else "—")
col3.metric("Overall Q1 Avg", f"{filtered['Question #1'].mean():.2f}" if len(filtered) else "—")

# Question averages
st.subheader("Average Score by Question")
q_means = filtered[question_cols].mean().to_frame("Average").reset_index().rename(columns={"index": "Question"})
st.bar_chart(q_means.set_index("Question"))

# Breakdowns
st.subheader("Breakdowns")

c1, c2 = st.columns(2)

with c1:
    st.write("Average by Gender")
    gender_means = filtered.groupby("Gender")[question_cols + ["Avg Score"]].mean()
    st.dataframe(gender_means.round(2), use_container_width=True)

with c2:
    st.write("Average by Age Group")
    age_means = filtered.groupby("Age")[question_cols + ["Avg Score"]].mean()
    st.dataframe(age_means.round(2), use_container_width=True)

# Optional: participant-level view
st.subheader("Participant Comparison (Average Score)")
participant_scores = filtered[["Participant", "Avg Score"]].set_index("Participant").sort_values("Avg Score", ascending=False)
st.bar_chart(participant_scores)
