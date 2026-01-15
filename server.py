from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

# Shared state
timer_state = {
    "last_command": None 
}

# Simple HTML Template with CSS for nice buttons
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Timer Remote</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; margin: 0; background: #111; color: white; }
        h1 { margin-bottom: 30px; }
        .btn { width: 200px; padding: 20px; margin: 10px; font-size: 1.2rem; font-weight: bold; border: none; border-radius: 8px; cursor: pointer; transition: opacity 0.2s; }
        .btn-toggle { background-color: #00883A; color: white; }
        .btn-reset { background-color: #444; color: white; }
        .btn:active { opacity: 0.7; }
    </style>
</head>
<body>
    <h1>Timer Remote</h1>
    <form action="/toggle" method="POST">
        <button type="submit" class="btn btn-toggle">START / PAUSE</button>
    </form>
    <form action="/reset" method="POST">
        <button type="submit" class="btn btn-reset">RESET</button>
    </form>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

@app.route('/status', methods=['GET'])
def get_status():
    response = jsonify(timer_state.copy())
    timer_state["last_command"] = None 
    return response

@app.route('/toggle', methods=['GET', 'POST'])
def trigger_toggle():
    timer_state["last_command"] = "toggle"
    # Redirect back to home if accessed via browser button
    return render_template_string(HTML_PAGE)

@app.route('/reset', methods=['GET', 'POST'])
def trigger_reset():
    timer_state["last_command"] = "reset"
    return render_template_string(HTML_PAGE)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)