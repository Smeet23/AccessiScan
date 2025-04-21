import subprocess
import tempfile
import json
import os

def analyze_accessibility(input_data, input_type):
    """
    Executes Node.js script to perform accessibility analysis.
    """
    node_script_path = os.path.join('scanner', 'scan_url.js' if input_type == 'url' else 'scan_html.js')

    if not os.path.exists(node_script_path):
        raise Exception(f"Node.js script not found at {node_script_path}")

    try:
        if input_type == 'url':
            result = subprocess.run(['node', node_script_path, input_data], capture_output=True, text=True)
        else:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w') as temp_file:
                temp_file.write(input_data)
                temp_path = temp_file.name

            result = subprocess.run(['node', node_script_path, temp_path], capture_output=True, text=True)
            os.unlink(temp_path)

        if result.returncode != 0:
            raise Exception(f"Error from accessibility scanner: {result.stderr}\n{result.stdout}")

        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            raise Exception(f"Error parsing JSON from accessibility scanner output: {e}")

        # Optional: reformat into your existing format
        summary = {
            "total_violations": len(data["violations"]),
            "critical": sum(1 for v in data["violations"] if v["impact"] == "critical"),
            "serious": sum(1 for v in data["violations"] if v["impact"] == "serious"),
            "moderate": sum(1 for v in data["violations"] if v["impact"] == "moderate"),
            "minor": sum(1 for v in data["violations"] if v["impact"] == "minor"),
        }

        return {
            "summary": summary,
            "violations": data["violations"]
        }
    
    except Exception as e:
        raise Exception(f"An error occurred during accessibility analysis: {str(e)}")
