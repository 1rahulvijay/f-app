from flask import Blueprint, render_template, jsonify, send_from_directory
from .. import engines, logger
from sqlalchemy.sql import text

dashboard_bp = Blueprint('dashboard', __name__)

def generate_time_series():
    try:
        with engines['db1'].connect() as connection:
            query = """
                SELECT 
                    TO_CHAR(month_end, 'Mon YY') AS month_end,
                    count_id,
                    count_gf,
                    count_gfc,
                    total_tf,
                    ocm_overall,
                    tasks_completed,
                    avg_completion_time,
                    efficiency_rate,
                    total_fte,
                    utilization,
                    overtime_hours
                FROM metrics_time_series
                WHERE month_end >= ADD_MONTHS(SYSDATE, -12)
                ORDER BY month_end DESC
            """
            result = connection.execute(text(query)).fetchall()
            data = [
                {
                    "month_end": row[0],
                    "count_id": int(row[1]),
                    "count_gf": int(row[2]),
                    "count_gfc": int(row[3]),
                    "total_tf": round(float(row[4]), 2),
                    "ocm_overall": round(float(row[5]), 2),
                    "tasks_completed": int(row[6]),
                    "avg_completion_time": float(row[7]),
                    "efficiency_rate": float(row[8]),
                    "total_fte": float(row[9]),
                    "utilization": float(row[10]),
                    "overtime_hours": float(row[11])
                }
                for row in result
            ]
            return data
    except Exception as e:
        logger.error(f"Error fetching time series data from DB1: {e}")
        return []

def generate_sankey_data():
    try:
        with engines['db2'].connect() as connection:
            # Query 1: Fetch nodes
            nodes_query = """
                SELECT name
                FROM sankey_nodes
                ORDER BY node_id
            """
            nodes_result = connection.execute(text(nodes_query)).fetchall()
            nodes = [{"name": row[0]} for row in nodes_result]

            # Query 2: Fetch links
            links_query = """
                SELECT source_node_id, target_node_id, value
                FROM sankey_links
                WHERE value > 0
            """
            links_result = connection.execute(text(links_query)).fetchall()
            links = [
                {
                    "source": int(row[0]),
                    "target": int(row[1]),
                    "value": float(row[2])
                }
                for row in links_result
            ]

            # Query 3: Calculate total flow
            total_flow_query = """
                SELECT SUM(value) AS total_flow
                FROM sankey_links
                WHERE value > 0
            """
            total_flow = connection.execute(text(total_flow_query)).scalar() or 0

            # Query 4: Count verticals
            verticals_query = """
                SELECT COUNT(*) 
                FROM sankey_nodes 
                WHERE name IN ('Retail', 'Technology', 'Education', 'Finance', 'Manufacturing', 'Healthcare')
            """
            verticals_count = connection.execute(text(verticals_query)).scalar()
            average_flow_per_vertical = round(total_flow / verticals_count, 2) if verticals_count > 0 else 0

            # Query 5: Count total requests
            total_requests_query = """
                SELECT COUNT(*) 
                FROM sankey_links 
                WHERE value > 0
            """
            total_requests = connection.execute(text(total_requests_query)).scalar()

            metrics = [
                {"label": "Total Flow", "value": float(total_flow)},
                {"label": "Avg Flow per Vertical", "value": average_flow_per_vertical},
                {"label": "Total Requests", "value": total_requests}
            ]

            return {"nodes": nodes, "links": links, "metrics": metrics}
    except Exception as e:
        logger.error(f"Error fetching Sankey data from DB2: {e}")
        return {"nodes": [], "links": [], "metrics": []}

@dashboard_bp.route('/')
def index():
    return render_template('index.html')

@dashboard_bp.route('/productivity')
def productivity():
    return render_template('productivity.html')

@dashboard_bp.route('/fte')
def fte():
    return render_template('fte.html')

@dashboard_bp.route('/sankey')
def sankey():
    return render_template('sankey.html')

@dashboard_bp.route('/combined')
def combined():
    return render_template('combined.html')

@dashboard_bp.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@dashboard_bp.route('/api/data')
def get_data():
    data = generate_time_series()
    if not data:
        logger.error("No data available for /api/data")
        return jsonify({"error": "No data available"}), 500
    current_month = data[0]
    prev_month = data[1] if len(data) > 1 else None
    trends = {
        "count_id_trend": "↑" if prev_month and current_month["count_id"] > prev_month["count_id"] else "↓",
        "count_gf_trend": "↑" if prev_month and current_month["count_gf"] > prev_month["count_gf"] else "↓",
        "count_gfc_trend": "↑" if prev_month and current_month["count_gfc"] > prev_month["count_gfc"] else "↓",
        "count_id_percent_change": round(((current_month["count_id"] - prev_month["count_id"]) / prev_month["count_id"]) * 100, 2) if prev_month and prev_month["count_id"] != 0 else 0,
        "count_gf_percent_change": round(((current_month["count_gf"] - prev_month["count_gf"]) / prev_month["count_gf"]) * 100, 2) if prev_month and prev_month["count_gf"] != 0 else 0,
        "count_gfc_percent_change": round(((current_month["count_gfc"] - prev_month["count_gfc"]) / prev_month["count_gfc"]) * 100, 2) if prev_month and prev_month["count_gfc"] != 0 else 0,
    }
    response = {
        "lineData": [{"label": d["month_end"], "value": d["count_id"]} for d in data],
        "barData": [{"label": d["month_end"], "value": d["count_gf"]} for d in data],
        "areaData": [{"label": d["month_end"], "value": d["count_gfc"]} for d in data],
        "scatterData": [{"label": d["month_end"], "total_tf": d["total_tf"], "ocm_overall": d["ocm_overall"]} for d in data],
        "metrics": {
            "current_metrics": {
                "count_id": current_month["count_id"],
                "count_gf": current_month["count_gf"],
                "count_gfc": current_month["count_gfc"],
                "trends": trends
            }
        }
    }
    logger.info(f"/api/data response generated")
    return jsonify(response)

@dashboard_bp.route('/api/productivity_data')
def get_productivity_data():
    data = generate_time_series()
    if not data:
        logger.error("No data available for /api/productivity_data")
        return jsonify({"error": "No data available"}), 500
    current_month = data[0]
    prev_month = data[1] if len(data) > 1 else None
    trends = {
        "tasks_completed_trend": "↑" if prev_month and current_month["tasks_completed"] > prev_month["tasks_completed"] else "↓",
        "avg_completion_time_trend": "↓" if prev_month and current_month["avg_completion_time"] < prev_month["avg_completion_time"] else "↑",
        "efficiency_rate_trend": "↑" if prev_month and current_month["efficiency_rate"] > prev_month["efficiency_rate"] else "↓",
        "tasks_completed_percent_change": round(((current_month["tasks_completed"] - prev_month["tasks_completed"]) / prev_month["tasks_completed"]) * 100, 2) if prev_month and prev_month["tasks_completed"] != 0 else 0,
        "avg_completion_time_percent_change": round(((current_month["avg_completion_time"] - prev_month["avg_completion_time"]) / prev_month["avg_completion_time"]) * 100, 2) if prev_month and prev_month["avg_completion_time"] != 0 else 0,
        "efficiency_rate_percent_change": round(((current_month["efficiency_rate"] - prev_month["efficiency_rate"]) / prev_month["efficiency_rate"]) * 100, 2) if prev_month and prev_month["efficiency_rate"] != 0 else 0,
    }
    response = {
        "lineData": [{"label": d["month_end"], "value": d["tasks_completed"]} for d in data],
        "barData": [{"label": d["month_end"], "value": d["avg_completion_time"]} for d in data],
        "areaData": [{"label": d["month_end"], "value": d["efficiency_rate"]} for d in data],
        "metrics": {
            "current_metrics": {
                "tasks_completed": current_month["tasks_completed"],
                "avg_completion_time": current_month["avg_completion_time"],
                "efficiency_rate": current_month["efficiency_rate"],
                "trends": trends
            }
        }
    }
    logger.info(f"/api/productivity_data response generated")
    return jsonify(response)

@dashboard_bp.route('/api/fte_data')
def get_fte_data():
    data = generate_time_series()
    if not data:
        logger.error("No data available for /api/fte_data")
        return jsonify({"error": "No data available"}), 500
    current_month = data[0]
    prev_month = data[1] if len(data) > 1 else None
    trends = {
        "total_fte_trend": "↑" if prev_month and current_month["total_fte"] > prev_month["total_fte"] else "↓",
        "utilization_trend": "↑" if prev_month and current_month["utilization"] > prev_month["utilization"] else "↓",
        "overtime_hours_trend": "↓" if prev_month and current_month["overtime_hours"] < prev_month["overtime_hours"] else "↑",
        "total_fte_percent_change": round(((current_month["total_fte"] - prev_month["total_fte"]) / prev_month["total_fte"]) * 100, 2) if prev_month and prev_month["total_fte"] != 0 else 0,
        "utilization_percent_change": round(((current_month["utilization"] - prev_month["utilization"]) / prev_month["utilization"]) * 100, 2) if prev_month and prev_month["utilization"] != 0 else 0,
        "overtime_hours_percent_change": round(((current_month["overtime_hours"] - prev_month["overtime_hours"]) / prev_month["overtime_hours"]) * 100, 2) if prev_month and prev_month["overtime_hours"] != 0 else 0,
    }
    response = {
        "lineData": [{"label": d["month_end"], "value": d["total_fte"]} for d in data],
        "barData": [{"label": d["month_end"], "value": d["utilization"]} for d in data],
        "areaData": [{"label": d["month_end"], "value": d["overtime_hours"]} for d in data],
        "metrics": {
            "current_metrics": {
                "total_fte": current_month["total_fte"],
                "utilization": current_month["utilization"],
                "overtime_hours": current_month["overtime_hours"],
                "trends": trends
            }
        }
    }
    logger.info(f"/api/fte_data response generated")
    return jsonify(response)

@dashboard_bp.route('/api/sankey_data')
def get_sankey_data():
    data = generate_sankey_data()
    if not data["nodes"] or not data["links"]:
        logger.error("No data available for /api/sankey_data")
        return jsonify({"error": "No data available"}), 500
    response = {"nodes": data["nodes"], "links": data["links"], "metrics": data["metrics"]}
    logger.info(f"/api/sankey_data response generated")
    return jsonify(response)
