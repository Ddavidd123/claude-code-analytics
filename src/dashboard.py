"""
Interactive Dashboard for Claude Code Telemetry Analytics

Built with Streamlit for real-time data visualization.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from data_processor import process_telemetry
from analytics import TelemetryAnalytics, generate_insights


def setup_page():
    """Configure Streamlit page settings."""
    st.set_page_config(
        page_title="Claude Code Analytics",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    st.markdown("""
        <style>
            .metric-card {
                background-color: #f0f2f6;
                padding: 20px;
                border-radius: 10px;
                margin: 10px 0;
            }
        </style>
    """, unsafe_allow_html=True)


@st.cache_data(show_spinner="⏳ Loading telemetry data... (first run ~1-2 min, cached after)")
def load_data():
    """Load and cache processed data with Streamlit memoization."""
    telemetry_file = "output/telemetry_logs.jsonl"
    employees_file = "output/employees.csv"
    
    # Check if files exist
    if not Path(telemetry_file).exists():
        st.error(f"❌ Telemetry file not found: {telemetry_file}")
        return None, None
    if not Path(employees_file).exists():
        st.error(f"❌ Employees file not found: {employees_file}")
        return None, None
    
    try:
        # Always reprocess when load_data is called so that real‑time
        # appends to the telemetry log are reflected after Refresh.
        events_df, users_df = process_telemetry(
            telemetry_file,
            employees_file,
            force_reprocess=True,
        )
        return events_df, users_df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        import traceback
        st.write(traceback.format_exc())
        return None, None


def display_overview(analytics: TelemetryAnalytics):
    """Display overview metrics."""
    st.markdown("## 📈 Platform Overview")
    
    stats = analytics.get_overall_statistics()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Users", stats['total_users'], delta=None)
    with col2:
        st.metric("Total Sessions", stats['total_sessions'], delta=None)
    with col3:
        st.metric("Total API Calls", stats['total_api_calls'], delta=None)
    with col4:
        st.metric("Total Cost (USD)", f"${stats['total_cost_usd']:.2f}", delta=None)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total Input Tokens", f"{stats['total_input_tokens']:,}", delta=None)
    with col2:
        st.metric("Total Output Tokens", f"{stats['total_output_tokens']:,}", delta=None)


def display_model_analysis(analytics: TelemetryAnalytics):
    """Display model usage analysis."""
    st.markdown("## 🤖 Model Usage Analysis")
    
    model_df = analytics.get_model_usage().reset_index()
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.bar(
            model_df.sort_values('total_cost', ascending=True),
            x='total_cost',
            y='model',
            orientation='h',
            title="Total Cost by Model",
            labels={'total_cost': 'Cost (USD)', 'model': 'Model'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.bar(
            model_df.sort_values('num_calls', ascending=True),
            x='num_calls',
            y='model',
            orientation='h',
            title="Number of API Calls by Model",
            labels={'num_calls': 'Calls', 'model': 'Model'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("### Model Performance Metrics")
    st.dataframe(model_df, use_container_width=True, hide_index=True)


def display_tool_analysis(analytics: TelemetryAnalytics):
    """Display tool usage analysis."""
    st.markdown("## 🔧 Tool Usage Analysis")
    
    tool_df = analytics.get_tool_usage().copy()
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.bar(
            tool_df.nlargest(10, 'num_decisions'),
            x='num_decisions',
            y='tool',
            orientation='h',
            title="Top 10 Tools by Usage",
            labels={'num_decisions': 'Number of Decisions', 'tool': 'Tool'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.bar(
            tool_df[tool_df['num_decisions'] > 0],
            x='success_rate',
            y='tool',
            orientation='h',
            title="Tool Success Rates",
            labels={'success_rate': 'Success Rate', 'tool': 'Tool'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("### Tool Detailed Stats")
    st.dataframe(tool_df, use_container_width=True, hide_index=True)


def display_user_segments(analytics: TelemetryAnalytics):
    """Display user segmentation."""
    st.markdown("## 👥 User Segmentation")
    
    segments = analytics.get_user_segments()
    
    if 'by_level' in segments:
        st.markdown("### Users by Level")
        level_df = segments['by_level'].reset_index()
        
        col1, col2 = st.columns(2)
        with col1:
            fig = px.bar(
                level_df,
                x='level',
                y='num_users',
                title="Number of Users by Level",
                labels={'num_users': 'Users', 'level': 'Level'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.bar(
                level_df,
                x='level',
                y='total_cost',
                title="Total Cost by Level",
                labels={'total_cost': 'Cost (USD)', 'level': 'Level'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        st.dataframe(level_df, use_container_width=True, hide_index=True)
    
    if 'by_practice' in segments:
        st.markdown("### Users by Practice")
        practice_df = segments['by_practice'].reset_index()
        
        fig = px.pie(
            practice_df,
            values='num_users',
            names='practice',
            title="User Distribution by Practice"
        )
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(practice_df, use_container_width=True, hide_index=True)
    
    if 'by_location' in segments:
        st.markdown("### Users by Location")
        location_df = segments['by_location'].reset_index()
        
        fig = px.bar(
            location_df.sort_values('num_users', ascending=True),
            x='num_users',
            y='location',
            orientation='h',
            title="Users by Location",
            labels={'num_users': 'Users', 'location': 'Location'}
        )
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(location_df, use_container_width=True, hide_index=True)


def display_top_users(analytics: TelemetryAnalytics):
    """Display top users."""
    st.markdown("## ⭐ Top Users")
    
    top_users = analytics.get_top_users(20)
    
    st.dataframe(top_users, use_container_width=True, hide_index=True)
    
    # Visualization
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.bar(
            top_users.head(10),
            x='cost_usd',
            y='email',
            orientation='h',
            title="Top 10 Users by Cost",
            labels={'cost_usd': 'Cost (USD)', 'email': 'User'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.bar(
            top_users.head(10),
            x='api_calls',
            y='email',
            orientation='h',
            title="Top 10 Users by API Calls",
            labels={'api_calls': 'API Calls', 'email': 'User'}
        )
        st.plotly_chart(fig, use_container_width=True)


def display_performance_metrics(analytics: TelemetryAnalytics):
    """Display performance metrics."""
    st.markdown("## ⚡ Performance Metrics")
    
    metrics = analytics.get_performance_metrics()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Avg API Duration (ms)", f"{metrics['avg_api_duration_ms']:.0f}")
    with col2:
        st.metric("Median API Duration (ms)", f"{metrics['median_api_duration_ms']:.0f}")
    with col3:
        st.metric("P95 API Duration (ms)", f"{metrics['p95_api_duration_ms']:.0f}")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Tool Success Rate", f"{metrics['tool_success_rate']:.1%}")
    with col2:
        st.metric("Avg Tool Duration (ms)", f"{metrics['avg_tool_duration_ms']:.0f}")
    with col3:
        st.metric("Cache Hit Ratio", f"{metrics['cache_hit_ratio']:.1%}")


def display_error_analysis(analytics: TelemetryAnalytics):
    """Display error analysis."""
    st.markdown("## ⚠️ Error Analysis")
    
    errors = analytics.get_error_analysis()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total Errors", errors['total_errors'])
    with col2:
        st.metric("Error Rate", f"{errors['error_rate']:.1%}")
    
    if errors['errors_by_type']:
        st.markdown("### Errors by Type")
        error_df = pd.DataFrame(list(errors['errors_by_type'].items()), columns=['Error Type', 'Count'])
        
        fig = px.bar(
            error_df.sort_values('Count', ascending=True),
            x='Count',
            y='Error Type',
            orientation='h',
            title="Error Distribution",
            labels={'Count': 'Number of Errors', 'Error Type': 'Error'}
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.dataframe(error_df, use_container_width=True, hide_index=True)


def main():
    """Main dashboard application."""
    setup_page()
    
    st.title("📊 Claude Code Analytics Dashboard")
    st.markdown("---")
    
    # Sidebar - always visible
    page = st.sidebar.radio(
        "📍 Navigation",
        ["Overview", "Models", "Tools", "Users", "Top Users", "Performance", "Errors"]
    )
    
    st.sidebar.markdown("---")
    st.sidebar.info("💡 This dashboard provides insights into Claude Code telemetry data.")
    st.sidebar.markdown("---")
    
    # Refresh button - ALWAYS visible, even during loading
    if st.sidebar.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()
    
    st.sidebar.markdown("---")
    st.sidebar.write("💡 For real-time demos, generate events using `realtime.simulate_stream` and hit Refresh above.")
    
    # Load data
    events_df, users_df = load_data()
    
    if events_df is None or users_df is None:
        return

    analytics = TelemetryAnalytics(events_df, users_df)
    
    # Display selected page
    if page == "Overview":
        display_overview(analytics)
        st.markdown("---")
        display_performance_metrics(analytics)
    elif page == "Models":
        display_model_analysis(analytics)
    elif page == "Tools":
        display_tool_analysis(analytics)
    elif page == "Users":
        display_user_segments(analytics)
    elif page == "Top Users":
        display_top_users(analytics)
    elif page == "Performance":
        display_performance_metrics(analytics)
    elif page == "Errors":
        display_error_analysis(analytics)


if __name__ == "__main__":
    main()
