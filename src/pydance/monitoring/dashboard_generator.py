"""
Dashboard generator for Pydance monitoring.
Creates web dashboards for monitoring data visualization.
"""

from typing import Dict, Any, Optional, List
import json
import time
from dataclasses import dataclass


@dataclass
class DashboardConfig:
    """Dashboard configuration"""

    title: str = "Pydance Monitoring Dashboard"
    refresh_interval: int = 30  # seconds
    theme: str = "dark"
    layout: str = "grid"


class DashboardGenerator:
    """Generates monitoring dashboards"""

    def __init__(self, config: Optional[DashboardConfig] = None):
        self.config = config or DashboardConfig()
        self.metrics_collector = None
        self.alert_manager = None

    def set_metrics_collector(self, collector):
        """Set the metrics collector"""
        self.metrics_collector = collector

    def set_alert_manager(self, manager):
        """Set the alert manager"""
        self.alert_manager = manager

    def generate_dashboard_html(self) -> str:
        """Generate HTML dashboard"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{self.config.title}</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: {'#1a1a1a' if self.config.theme == 'dark' else '#ffffff'};
                    color: {'#ffffff' if self.config.theme == 'dark' else '#000000'};
                }}
                .dashboard-title {{
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .metrics-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 20px;
                }}
                .metric-card {{
                    background-color: {'#2d2d2d' if self.config.theme == 'dark' else '#f5f5f5'};
                    border-radius: 8px;
                    padding: 20px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .metric-title {{
                    font-size: 18px;
                    font-weight: bold;
                    margin-bottom: 10px;
                }}
                .metric-value {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #007bff;
                }}
                .alert-section {{
                    margin-top: 40px;
                }}
                .alert-item {{
                    background-color: #dc3545;
                    color: white;
                    padding: 10px;
                    margin: 5px 0;
                    border-radius: 4px;
                }}
                .refresh-info {{
                    text-align: center;
                    margin-top: 20px;
                    color: #666;
                }}
            </style>
        </head>
        <body>
            <h1 class="dashboard-title">{self.config.title}</h1>

            <div class="metrics-grid" id="metrics-container">
                {self._generate_metrics_html()}
            </div>

            <div class="alert-section" id="alerts-container">
                {self._generate_alerts_html()}
            </div>

            <div class="refresh-info">
                Last updated: <span id="last-update">{time.strftime('%Y-%m-%d %H:%M:%S')}</span>
                (Refreshes every {self.config.refresh_interval} seconds)
            </div>

            <script>
                function updateDashboard() {{
                    fetch('/api/monitoring/metrics')
                        .then(response => response.json())
                        .then(data => {{
                            document.getElementById('metrics-container').innerHTML = generateMetricsHTML(data);
                            document.getElementById('last-update').textContent = new Date().toLocaleString();
                        }})
                        .catch(error => console.error('Error updating dashboard:', error));
                }}

                function generateMetricsHTML(data) {{
                    // Generate metrics HTML from data
                    return '<div class="metric-card"><div class="metric-title">Metrics</div><div class="metric-value">' + (data.length || 0) + '</div></div>';
                }}

                // Auto-refresh
                setInterval(updateDashboard, {self.config.refresh_interval * 1000});
            </script>
        </body>
        </html>
        """
        return html

    def generate_dashboard_json(self) -> Dict[str, Any]:
        """Generate dashboard data as JSON"""
        return {
            "title": self.config.title,
            "timestamp": time.time(),
            "metrics": self._get_metrics_data(),
            "alerts": self._get_alerts_data(),
            "config": {
                "theme": self.config.theme,
                "refresh_interval": self.config.refresh_interval
            }
        }

    def _generate_metrics_html(self) -> str:
        """Generate HTML for metrics display"""
        if not self.metrics_collector:
            return '<div class="metric-card"><div class="metric-title">Metrics Collector</div><div class="metric-value">Not Available</div></div>'

        try:
            # Get basic metrics info
            metrics_count = len(self.metrics_collector._metrics)
            return f'''
                <div class="metric-card">
                    <div class="metric-title">Total Metrics</div>
                    <div class="metric-value">{metrics_count}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">Active Collectors</div>
                    <div class="metric-value">{len(self.metrics_collector._collectors)}</div>
                </div>
            '''
        except Exception:
            return '<div class="metric-card"><div class="metric-title">Metrics</div><div class="metric-value">Error</div></div>'

    def _generate_alerts_html(self) -> str:
        """Generate HTML for alerts display"""
        if not self.alert_manager:
            return '<h2>Alerting System</h2><p>Not Available</p>'

        try:
            active_alerts = self.alert_manager.get_active_alerts()
            if not active_alerts:
                return '<h2>Active Alerts</h2><p>No active alerts</p>'

            alerts_html = '<h2>Active Alerts</h2>'
            for alert in active_alerts:
                alerts_html += f'''
                    <div class="alert-item">
                        <strong>{alert.severity.value.upper()}</strong>: {alert.message}
                        <br><small>{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(alert.timestamp))}</small>
                    </div>
                '''

            return alerts_html
        except Exception:
            return '<h2>Alerts</h2><p>Error loading alerts</p>'

    def _get_metrics_data(self) -> List[Dict[str, Any]]:
        """Get metrics data"""
        if not self.metrics_collector:
            return []

        try:
            all_values = self.metrics_collector.collect_all()
            return [v.__dict__ for v in all_values]
        except Exception:
            return []

    def _get_alerts_data(self) -> List[Dict[str, Any]]:
        """Get alerts data"""
        if not self.alert_manager:
            return []

        try:
            active_alerts = self.alert_manager.get_active_alerts()
            return [alert.__dict__ for alert in active_alerts]
        except Exception:
            return []