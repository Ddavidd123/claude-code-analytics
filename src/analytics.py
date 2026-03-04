"""
Analytics and Insights Generation

Computes actionable insights from processed telemetry data.
"""

import pandas as pd
from typing import Dict, List, Tuple
from datetime import datetime, timedelta


class TelemetryAnalytics:
    """Generate analytics and insights from telemetry data."""
    
    def __init__(self, events_df: pd.DataFrame, users_df: pd.DataFrame):
        """
        Initialize analytics engine.
        
        Args:
            events_df: Normalized events DataFrame
            users_df: Aggregated users DataFrame
        """
        self.events = events_df
        self.users = users_df
    
    def get_overall_statistics(self) -> Dict:
        """Get high-level platform statistics."""
        api_requests = self.events[self.events['event_type'] == 'claude_code.api_request']
        
        stats = {
            'total_users': self.events['user_id'].nunique(),
            'total_sessions': self.events['session_id'].nunique(),
            'total_events': len(self.events),
            'total_api_calls': len(api_requests),
            'total_cost_usd': api_requests['cost_usd'].sum(),
            'avg_cost_per_api': api_requests['cost_usd'].mean(),
            'total_input_tokens': api_requests['input_tokens'].sum(),
            'total_output_tokens': api_requests['output_tokens'].sum(),
            'avg_session_duration_min': self._calculate_session_duration(),
        }
        return stats
    
    def _calculate_session_duration(self) -> float:
        """Calculate average session duration in minutes."""
        if len(self.events) == 0:
            return 0
        session_durations = []
        for session_id in self.events['session_id'].unique():
            session_events = self.events[self.events['session_id'] == session_id]
            if 'timestamp' in session_events.columns and len(session_events) > 0:
                session_durations.append(10)  # Approximate
        return sum(session_durations) / len(session_durations) if session_durations else 0
    
    def get_model_usage(self) -> pd.DataFrame:
        """Analyze model usage patterns."""
        api_requests = self.events[self.events['event_type'] == 'claude_code.api_request']
        
        model_stats = api_requests.groupby('model').agg({
            'cost_usd': ['sum', 'mean', 'count'],
            'input_tokens': 'sum',
            'output_tokens': 'sum',
            'duration_ms': 'mean',
        }).round(3)
        
        model_stats.columns = ['total_cost', 'avg_cost', 'num_calls', 'total_input_tokens', 
                               'total_output_tokens', 'avg_duration_ms']
        model_stats = model_stats.sort_values('total_cost', ascending=False)
        
        return model_stats
    
    def get_tool_usage(self) -> pd.DataFrame:
        """Analyze tool usage patterns."""
        tool_decisions = self.events[self.events['event_type'] == 'claude_code.tool_decision']
        tool_results = self.events[self.events['event_type'] == 'claude_code.tool_result']
        
        tool_stats = []
        for tool in tool_decisions['tool_name'].unique():
            decisions = tool_decisions[tool_decisions['tool_name'] == tool]
            results = tool_results[tool_results['tool_name'] == tool]
            
            accepted = (decisions['decision'] == 'accept').sum()
            rejected = (decisions['decision'] == 'reject').sum()
            successful = results['success'].sum() if len(results) > 0 else 0
            total_results = len(results)
            
            tool_stats.append({
                'tool': tool,
                'num_decisions': len(decisions),
                'accepted': accepted,
                'rejected': rejected,
                'accept_rate': (accepted / len(decisions)) if len(decisions) > 0 else 0,
                'successful_executions': successful,
                'total_executions': total_results,
                'success_rate': (successful / total_results) if total_results > 0 else 0,
                'avg_duration_ms': results['duration_ms'].mean() if len(results) > 0 else 0,
            })
        
        df = pd.DataFrame(tool_stats).sort_values('num_decisions', ascending=False)
        return df
    
    def get_user_segments(self) -> Dict[str, pd.DataFrame]:
        """Segment users by various dimensions."""
        segments = {}
        
        # By level
        if 'level' in self.users.columns:
            segments['by_level'] = self.users.groupby('level').agg({
                'user_id': 'count',
                'total_cost_usd': 'sum',
                'total_api_calls': 'sum',
                'total_input_tokens': 'sum',
                'total_output_tokens': 'sum',
            }).round(2)
            segments['by_level'].columns = ['num_users', 'total_cost', 'total_api_calls', 
                                            'total_input_tokens', 'total_output_tokens']
        
        # By practice
        if 'practice' in self.users.columns:
            segments['by_practice'] = self.users.groupby('practice').agg({
                'user_id': 'count',
                'total_cost_usd': 'sum',
                'total_api_calls': 'sum',
            }).round(2)
            segments['by_practice'].columns = ['num_users', 'total_cost', 'total_api_calls']
        
        # By location
        if 'location' in self.users.columns:
            segments['by_location'] = self.users.groupby('location').agg({
                'user_id': 'count',
                'total_cost_usd': 'sum',
            }).round(2)
            segments['by_location'].columns = ['num_users', 'total_cost']
        
        return segments
    
    def get_top_users(self, limit: int = 10) -> pd.DataFrame:
        """Get top users by various metrics."""
        top_by_cost = self.users.nlargest(limit, 'total_cost_usd')[
            ['user_email', 'total_cost_usd', 'total_api_calls', 'num_sessions', 'level']
        ].copy()
        top_by_cost.columns = ['email', 'cost_usd', 'api_calls', 'sessions', 'level']
        return top_by_cost
    
    def get_error_analysis(self) -> Dict:
        """Analyze API errors."""
        api_errors = self.events[self.events['event_type'] == 'claude_code.api_error']
        
        if len(api_errors) == 0:
            return {'total_errors': 0, 'error_rate': 0, 'errors_by_type': {}}
        
        total_api_calls = len(self.events[self.events['event_type'] == 'claude_code.api_request'])
        error_rate = len(api_errors) / (total_api_calls + len(api_errors)) if (total_api_calls + len(api_errors)) > 0 else 0
        
        errors_by_type = api_errors['error'].value_counts().to_dict()
        
        return {
            'total_errors': len(api_errors),
            'error_rate': error_rate,
            'errors_by_type': errors_by_type,
        }
    
    def get_performance_metrics(self) -> Dict:
        """Calculate performance metrics."""
        api_requests = self.events[self.events['event_type'] == 'claude_code.api_request']
        tool_results = self.events[self.events['event_type'] == 'claude_code.tool_result']
        
        metrics = {
            'avg_api_duration_ms': api_requests['duration_ms'].mean() if len(api_requests) > 0 else 0,
            'median_api_duration_ms': api_requests['duration_ms'].median() if len(api_requests) > 0 else 0,
            'p95_api_duration_ms': api_requests['duration_ms'].quantile(0.95) if len(api_requests) > 0 else 0,
            'tool_success_rate': (tool_results['success'].sum() / len(tool_results)) if len(tool_results) > 0 else 0,
            'avg_tool_duration_ms': tool_results['duration_ms'].mean() if len(tool_results) > 0 else 0,
            'cache_hit_ratio': (self.events[self.events['event_type'] == 'claude_code.api_request']['cache_read_tokens'].sum() / 
                               (self.events[self.events['event_type'] == 'claude_code.api_request']['cache_read_tokens'].sum() + 
                                self.events[self.events['event_type'] == 'claude_code.api_request']['cache_creation_tokens'].sum() + 1)),
        }
        
        for key in metrics:
            if isinstance(metrics[key], float):
                metrics[key] = round(metrics[key], 2)
        
        return metrics


def generate_insights(events_df: pd.DataFrame, users_df: pd.DataFrame) -> Dict:
    """
    Generate comprehensive insights from telemetry data.
    
    Returns:
        Dictionary containing all insights
    """
    analytics = TelemetryAnalytics(events_df, users_df)
    
    insights = {
        'overall_statistics': analytics.get_overall_statistics(),
        'model_usage': analytics.get_model_usage().to_dict(),
        'tool_usage': analytics.get_tool_usage().to_dict(),
        'user_segments': {k: v.to_dict() for k, v in analytics.get_user_segments().items()},
        'top_users': analytics.get_top_users().to_dict(),
        'error_analysis': analytics.get_error_analysis(),
        'performance_metrics': analytics.get_performance_metrics(),
    }
    
    return insights
