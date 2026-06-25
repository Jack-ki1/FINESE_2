from flask import Blueprint, render_template, session, jsonify, request, current_app

bp = Blueprint('chatbot', __name__)

@bp.route('/')
def chatbot_page():
    return render_template('chatbot.html', active_tab='chatbot')

@bp.route('/api/ask', methods=['POST'])
def ask():
    dataset_id = session.get('dataset_id')
    msg = request.json.get('message', '')
    model = request.json.get('model', 'openai')
    df, name = (None, None)
    if dataset_id:
        df, name = current_app.dataset_store.load(dataset_id)
    context = f"The dataset '{name}' has {len(df)} rows and {len(df.columns)} columns." if df is not None else "No dataset loaded."
    # TODO: Wire to services.llm_service for production
    reply = f"Echo: {msg}\n\nContext: {context}"
    history = session.get('chat_history', [])
    history.append({'role': 'user', 'content': msg})
    history.append({'role': 'assistant', 'content': reply})
    session['chat_history'] = history
    return jsonify({'reply': reply, 'history': history})
