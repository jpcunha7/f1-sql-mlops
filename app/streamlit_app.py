"""Streamlit app for F1 race predictions."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import duckdb

from f1sqlmlops.config import config
from f1sqlmlops.features.export_features import export_features, get_feature_columns
from f1sqlmlops.inference.predict import load_models, predict_race

# Page config
st.set_page_config(
    page_title="F1 Race Predictor",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #E10600;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #E10600;
    }
    .prediction-box {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_cached_models():
    """Load models with caching."""
    try:
        return load_models()
    except Exception as e:
        st.error(f"Failed to load models: {e}")
        return None


@st.cache_data
def load_cached_data():
    """Load data with caching."""
    try:
        splits = export_features()
        return splits
    except Exception as e:
        st.error(f"Failed to load data: {e}")
        return None


@st.cache_data
def load_dimension_tables():
    """Load driver, circuit, and race dimension tables from DuckDB."""
    try:
        conn = duckdb.connect(str(config.DUCKDB_PATH))

        # Load drivers
        drivers = conn.execute("""
            SELECT driver_id, full_name, nationality
            FROM main_marts.dim_driver
        """).df()

        # Load circuits
        circuits = conn.execute("""
            SELECT circuit_id, circuit_name, location, country
            FROM main_marts.dim_circuit
        """).df()

        # Load races (for race names)
        races = conn.execute("""
            SELECT race_id, race_name, year, round, circuit_id
            FROM main_marts.dim_race
        """).df()

        conn.close()

        return {
            'drivers': drivers,
            'circuits': circuits,
            'races': races
        }
    except Exception as e:
        st.error(f"Failed to load dimension tables: {e}")
        return None


def main():
    """Main Streamlit app."""

    # Header
    st.markdown('<h1 class="main-header">F1 Race Predictor</h1>', unsafe_allow_html=True)
    st.markdown("---")

    # Sidebar
    with st.sidebar:
        st.markdown("### Navigation")
        page = st.radio(
            "Select Page",
            ["Make Predictions", "Model Performance", "Feature Importance", "Historical Analysis"],
            label_visibility="collapsed"
        )

        st.markdown("---")
        st.markdown("### About")
        st.info(
            "This app predicts:\n"
            "- **Top-10 Finish** probability\n"
            "- **DNF (Did Not Finish)** probability\n\n"
            "Built with dbt, MLflow, and Streamlit"
        )

    # Load models and data
    models = load_cached_models()
    data_splits = load_cached_data()
    dim_tables = load_dimension_tables()

    if models is None or data_splits is None or dim_tables is None:
        st.error("Failed to initialize app. Please ensure models are trained and data is available.")
        return

    # Route to selected page
    if page == "Make Predictions":
        show_predictions_page(models, data_splits, dim_tables)
    elif page == "Model Performance":
        show_performance_page(models, data_splits, dim_tables)
    elif page == "Feature Importance":
        show_feature_importance_page(models)
    elif page == "Historical Analysis":
        show_historical_page(data_splits, dim_tables)


def show_predictions_page(models, data_splits, dim_tables):
    """Display predictions page."""
    st.header("Make Race Predictions")

    # Combine all data
    all_data = pd.concat([data_splits['train'], data_splits['val'], data_splits['test']], ignore_index=True)

    # Filters
    col1, col2 = st.columns(2)

    with col1:
        years = sorted(all_data['year'].unique(), reverse=True)
        selected_year = st.selectbox("Select Year", years)

    year_data = all_data[all_data['year'] == selected_year]

    with col2:
        # Create track selector using REAL circuit names from dimension table
        tracks_df = year_data.groupby('round').agg({
            'race_id': 'first',
            'circuit_id': 'first'
        }).reset_index()

        # Merge with races and circuits to get actual names
        tracks_df = tracks_df.merge(dim_tables['races'][['race_id', 'race_name']], on='race_id', how='left')
        tracks_df = tracks_df.merge(dim_tables['circuits'][['circuit_id', 'circuit_name']], on='circuit_id', how='left')

        # Create track labels with real circuit names
        track_labels = []
        for _, row in tracks_df.iterrows():
            circuit_name = row['circuit_name'] if pd.notna(row['circuit_name']) else f"Circuit {int(row['circuit_id'])}"
            race_name = row['race_name'] if pd.notna(row['race_name']) else f"Round {int(row['round'])}"
            track_labels.append(f"{circuit_name} ({race_name})")

        selected_track_idx = st.selectbox("Select Track", range(len(track_labels)), format_func=lambda x: track_labels[x])
        selected_race_id = tracks_df.iloc[selected_track_idx]['race_id']

    # Get race data
    race_data = all_data[all_data['race_id'] == selected_race_id].copy()

    if len(race_data) == 0:
        st.warning("No data found for selected race")
        return

    st.markdown("---")

    # Make predictions
    feature_cols, _ = get_feature_columns(race_data)
    predictions = predict_race(race_data, models, feature_cols)

    # FIX PREDICTION LOGIC: If DNF probability > 50%, predict DNF instead of top-10
    predictions['final_prediction'] = predictions.apply(
        lambda row: 'DNF' if row['dnf_probability'] > 0.5 else ('Top-10' if row['top10_probability'] > 0.5 else 'Outside Top-10'),
        axis=1
    )

    # Recalculate prediction counts based on corrected logic
    predictions['top10_prediction'] = (predictions['final_prediction'] == 'Top-10').astype(int)
    predictions['dnf_prediction'] = (predictions['final_prediction'] == 'DNF').astype(int)

    # Add REAL driver names from dimension table
    predictions = predictions.merge(
        dim_tables['drivers'][['driver_id', 'full_name', 'nationality']],
        on='driver_id',
        how='left'
    )
    # Fallback to driver ID if name not found
    predictions['driver_name'] = predictions['full_name'].fillna(predictions['driver_id'].astype(str))

    # Sort by grid position (starting order)
    predictions = predictions.sort_values('grid_position')

    # Display race info
    track_name = track_labels[selected_track_idx]
    st.subheader(f"{selected_year} - {track_name}")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Drivers", len(predictions))
    with col2:
        predicted_top10 = predictions['top10_prediction'].sum()
        st.metric("Predicted Top-10", f"{predicted_top10}")
    with col3:
        predicted_dnf = predictions['dnf_prediction'].sum()
        st.metric("Predicted DNFs", f"{predicted_dnf}")
    with col4:
        avg_dnf_prob = predictions['dnf_probability'].mean()
        st.metric("Avg DNF Prob", f"{avg_dnf_prob:.1%}")

    st.markdown("---")

    # Predictions table
    st.subheader("Driver Predictions")

    # Prepare display dataframe
    display_df = predictions[[
        'driver_name', 'grid_position', 'qualifying_position',
        'top10_probability', 'dnf_probability', 'final_prediction'
    ]].copy()

    display_df.columns = [
        'Driver', 'Grid Pos', 'Quali Pos',
        'Top-10 Prob', 'DNF Prob', 'Prediction'
    ]

    # Color code predictions with READABLE colors
    def highlight_prediction(row):
        if row['Prediction'] == 'Top-10':
            # Light green with dark text - readable
            return ['background-color: #90EE90; color: #000000'] * len(row)
        elif row['Prediction'] == 'DNF':
            # Light red with dark text - readable
            return ['background-color: #FFB6C1; color: #000000'] * len(row)
        else:
            # Light gray for outside top-10
            return ['background-color: #F0F0F0; color: #000000'] * len(row)

    styled_df = display_df.style.apply(highlight_prediction, axis=1).format({
        'Top-10 Prob': '{:.1%}',
        'DNF Prob': '{:.1%}',
    })

    st.dataframe(styled_df, use_container_width=True, height=400)

    # Visualization
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top-10 Probabilities")
        fig = px.bar(
            predictions.head(10),
            x='driver_name',
            y='top10_probability',
            title="All Drivers - Top-10 Finish Probability",
            labels={'driver_name': 'Driver', 'top10_probability': 'Probability'},
            color='top10_probability',
            color_continuous_scale='Greens'
        )
        fig.update_layout(showlegend=False, xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("DNF Risk")
        dnf_sorted = predictions.sort_values('dnf_probability', ascending=False).head(10)
        fig = px.bar(
            dnf_sorted,
            x='driver_name',
            y='dnf_probability',
            title="Drivers with Highest DNF Risk",
            labels={'driver_name': 'Driver', 'dnf_probability': 'Probability'},
            color='dnf_probability',
            color_continuous_scale='Reds'
        )
        fig.update_layout(showlegend=False, xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    # Show accuracy if ground truth available
    if 'target_top_10' in predictions.columns:
        st.markdown("---")
        st.subheader("Prediction Accuracy")

        col1, col2 = st.columns(2)
        with col1:
            top10_acc = (predictions['top10_prediction'] == predictions['target_top_10']).mean()
            st.metric("Top-10 Accuracy", f"{top10_acc:.1%}")
        with col2:
            dnf_acc = (predictions['dnf_prediction'] == predictions['target_dnf']).mean()
            st.metric("DNF Accuracy", f"{dnf_acc:.1%}")


def show_performance_page(models, data_splits, dim_tables):
    """Display model performance page."""
    st.header("Model Performance")

    # Test set performance
    test_data = data_splits['test']
    feature_cols, _ = get_feature_columns(test_data)

    predictions = predict_race(test_data, models, feature_cols)

    st.subheader("Test Set Performance (2019-2020)")

    # Overall metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Test Samples", len(test_data))
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        if 'target_top_10' in predictions.columns:
            top10_acc = (predictions['top10_prediction'] == predictions['target_top_10']).mean()
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Top-10 Accuracy", f"{top10_acc:.1%}")
            st.markdown('</div>', unsafe_allow_html=True)

    with col3:
        if 'target_dnf' in predictions.columns:
            dnf_acc = (predictions['dnf_prediction'] == predictions['target_dnf']).mean()
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("DNF Accuracy", f"{dnf_acc:.1%}")
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # Performance by year
    st.subheader("Performance by Year")

    if 'target_top_10' in predictions.columns:
        yearly_performance = predictions.groupby('year').apply(
            lambda x: pd.Series({
                'top10_accuracy': (x['top10_prediction'] == x['target_top_10']).mean(),
                'dnf_accuracy': (x['dnf_prediction'] == x['target_dnf']).mean(),
                'samples': len(x)
            }), include_groups=False
        ).reset_index()

        col1, col2 = st.columns(2)

        with col1:
            fig = px.bar(
                yearly_performance,
                x='year',
                y='top10_accuracy',
                title="Top-10 Accuracy by Year",
                labels={'year': 'Year', 'top10_accuracy': 'Accuracy'},
                text='top10_accuracy'
            )
            fig.update_traces(texttemplate='%{text:.1%}', textposition='outside')
            fig.update_layout(yaxis_range=[0, 1.1])
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.bar(
                yearly_performance,
                x='year',
                y='dnf_accuracy',
                title="DNF Accuracy by Year",
                labels={'year': 'Year', 'dnf_accuracy': 'Accuracy'},
                text='dnf_accuracy',
                color_discrete_sequence=['#E10600']
            )
            fig.update_traces(texttemplate='%{text:.1%}', textposition='outside')
            fig.update_layout(yaxis_range=[0, 1.1])
            st.plotly_chart(fig, use_container_width=True)

    # Confusion matrices
    st.markdown("---")
    st.subheader("Prediction Distribution")

    col1, col2 = st.columns(2)

    with col1:
        if 'target_top_10' in predictions.columns:
            from sklearn.metrics import confusion_matrix

            cm = confusion_matrix(predictions['target_top_10'], predictions['top10_prediction'])

            if cm.shape == (2, 2):
                cm_df = pd.DataFrame(
                    cm,
                    index=['Actual: No', 'Actual: Yes'],
                    columns=['Pred: No', 'Pred: Yes']
                )

                fig = px.imshow(
                    cm,
                    labels=dict(x="Predicted", y="Actual", color="Count"),
                    x=['No Top-10', 'Top-10'],
                    y=['No Top-10', 'Top-10'],
                    title="Top-10 Confusion Matrix",
                    text_auto=True,
                    color_continuous_scale='Greens'
                )
                st.plotly_chart(fig, use_container_width=True)

    with col2:
        if 'target_dnf' in predictions.columns:
            cm = confusion_matrix(predictions['target_dnf'], predictions['dnf_prediction'])

            if cm.shape == (2, 2):
                fig = px.imshow(
                    cm,
                    labels=dict(x="Predicted", y="Actual", color="Count"),
                    x=['No DNF', 'DNF'],
                    y=['No DNF', 'DNF'],
                    title="DNF Confusion Matrix",
                    text_auto=True,
                    color_continuous_scale='Reds'
                )
                st.plotly_chart(fig, use_container_width=True)


def show_feature_importance_page(models):
    """Display feature importance page."""
    st.header("Feature Importance Analysis")

    st.markdown("""
    Understanding which features drive the predictions helps interpret model behavior
    and identify the most important factors in F1 race outcomes.
    """)

    # Load feature importance from models
    col1, col2 = st.columns(2)

    with col1:
        if 'top10' in models:
            st.subheader("Top-10 Model Features")

            # Get feature importances
            model = models['top10']
            if hasattr(model.named_steps['classifier'], 'feature_importances_'):
                importances = model.named_steps['classifier'].feature_importances_

                # Load feature names
                models_dir = config.MODELS_DIR
                feature_file = models_dir / "top10_classifier_features.txt"

                if feature_file.exists():
                    with open(feature_file, 'r') as f:
                        feature_names = [line.strip() for line in f]

                    importance_df = pd.DataFrame({
                        'Feature': feature_names,
                        'Importance': importances
                    }).sort_values('Importance', ascending=False).head(15)

                    fig = px.bar(
                        importance_df,
                        x='Importance',
                        y='Feature',
                        orientation='h',
                        title="Top 15 Most Important Features",
                        labels={'Importance': 'Feature Importance'},
                        color='Importance',
                        color_continuous_scale='Greens'
                    )
                    fig.update_layout(yaxis={'categoryorder': 'total ascending'})
                    st.plotly_chart(fig, use_container_width=True)

                    with st.expander("View All Features"):
                        full_df = pd.DataFrame({
                            'Feature': feature_names,
                            'Importance': importances
                        }).sort_values('Importance', ascending=False)
                        st.dataframe(full_df, use_container_width=True)

    with col2:
        if 'dnf' in models:
            st.subheader("DNF Model Features")

            model = models['dnf']
            if hasattr(model.named_steps['classifier'], 'feature_importances_'):
                importances = model.named_steps['classifier'].feature_importances_

                models_dir = config.MODELS_DIR
                feature_file = models_dir / "dnf_classifier_features.txt"

                if feature_file.exists():
                    with open(feature_file, 'r') as f:
                        feature_names = [line.strip() for line in f]

                    importance_df = pd.DataFrame({
                        'Feature': feature_names,
                        'Importance': importances
                    }).sort_values('Importance', ascending=False).head(15)

                    fig = px.bar(
                        importance_df,
                        x='Importance',
                        y='Feature',
                        orientation='h',
                        title="Top 15 Most Important Features",
                        labels={'Importance': 'Feature Importance'},
                        color='Importance',
                        color_continuous_scale='Reds'
                    )
                    fig.update_layout(yaxis={'categoryorder': 'total ascending'})
                    st.plotly_chart(fig, use_container_width=True)

                    with st.expander("View All Features"):
                        full_df = pd.DataFrame({
                            'Feature': feature_names,
                            'Importance': importances
                        }).sort_values('Importance', ascending=False)
                        st.dataframe(full_df, use_container_width=True)

    st.markdown("---")

    # Feature descriptions
    st.subheader("Feature Descriptions")

    feature_descriptions = {
        "grid_position": "Starting grid position (lower is better)",
        "qualifying_position": "Qualifying session position",
        "driver_career_dnf_rate": "Historical DNF rate for this driver",
        "driver_top10_rate_recent": "Driver's top-10 rate in recent races",
        "driver_dnf_rate_recent": "Driver's DNF rate in recent races",
        "constructor_career_dnf_rate": "Historical DNF rate for this team",
        "constructor_top10_rate_recent": "Team's top-10 rate in recent races",
        "circuit_avg_dnf_rate": "Average DNF rate at this circuit",
        "driver_top10_rate_at_circuit": "Driver's historical top-10 rate at this circuit",
        "started_top_5": "Whether driver started in top 5 positions"
    }

    st.table(pd.DataFrame(list(feature_descriptions.items()), columns=['Feature', 'Description']))


def show_historical_page(data_splits, dim_tables):
    """Display historical analysis page."""
    st.header("Historical Race Analysis")

    # Combine all data
    all_data = pd.concat([data_splits['train'], data_splits['val'], data_splits['test']], ignore_index=True)

    # Overall statistics
    st.subheader("Dataset Overview")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Races", all_data['race_id'].nunique())
    with col2:
        st.metric("Total Results", len(all_data))
    with col3:
        years_range = f"{all_data['year'].min()}-{all_data['year'].max()}"
        st.metric("Years", years_range)
    with col4:
        # Show total unique drivers from dimension table
        total_drivers = len(dim_tables['drivers'])
        st.metric("Total Drivers", total_drivers)

    st.markdown("---")

    # Temporal splits
    st.subheader("Data Splits")

    split_stats = pd.DataFrame({
        'Split': ['Train', 'Validation', 'Test'],
        'Samples': [len(data_splits['train']), len(data_splits['val']), len(data_splits['test'])],
        'Years': [
            f"{data_splits['train']['year'].min()}-{data_splits['train']['year'].max()}" if len(data_splits['train']) > 0 else "N/A",
            f"{data_splits['val']['year'].min()}-{data_splits['val']['year'].max()}" if len(data_splits['val']) > 0 else "N/A",
            f"{data_splits['test']['year'].min()}-{data_splits['test']['year'].max()}" if len(data_splits['test']) > 0 else "N/A"
        ]
    })

    fig = px.bar(
        split_stats,
        x='Split',
        y='Samples',
        title="Temporal Split Distribution",
        text='Samples',
        color='Split',
        color_discrete_sequence=['#1f77b4', '#ff7f0e', '#2ca02c']
    )
    fig.update_traces(textposition='outside')
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Historical trends
    st.subheader("Historical Trends")

    if 'target_top_10' in all_data.columns and 'target_dnf' in all_data.columns:
        yearly_stats = all_data.groupby('year').agg({
            'target_top_10': 'mean',
            'target_dnf': 'mean',
            'race_id': 'count'
        }).reset_index()
        yearly_stats.columns = ['Year', 'Top-10 Rate', 'DNF Rate', 'Samples']

        col1, col2 = st.columns(2)

        with col1:
            fig = px.line(
                yearly_stats,
                x='Year',
                y='Top-10 Rate',
                title="Top-10 Finish Rate Over Time",
                markers=True
            )
            fig.update_layout(yaxis_tickformat='.1%')
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.line(
                yearly_stats,
                x='Year',
                y='DNF Rate',
                title="DNF Rate Over Time",
                markers=True,
                line_shape='spline',
                color_discrete_sequence=['#E10600']
            )
            fig.update_layout(yaxis_tickformat='.1%')
            st.plotly_chart(fig, use_container_width=True)

    # Feature distributions
    st.markdown("---")
    st.subheader("Feature Distributions")

    feature_to_plot = st.selectbox(
        "Select Feature to Analyze",
        ['grid_position', 'driver_top10_rate_recent', 'driver_dnf_rate_recent',
         'constructor_top10_rate_recent', 'circuit_avg_dnf_rate']
    )

    if feature_to_plot in all_data.columns:
        fig = px.histogram(
            all_data,
            x=feature_to_plot,
            title=f"Distribution of {feature_to_plot}",
            nbins=30,
            marginal="box"
        )
        st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    main()
