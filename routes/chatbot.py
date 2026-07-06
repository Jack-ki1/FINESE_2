from flask import Blueprint, render_template, session, jsonify, request, current_app
import pandas as pd
import numpy as np

bp = Blueprint('chatbot', __name__)

@bp.route('/')
def chatbot_page():
    return render_template('chatbot.html', active_tab='chatbot')

@bp.route('/api/configure', methods=['POST'])
def configure_api():
    """Securely store API key in session"""
    provider = request.json.get('provider')
    api_key = request.json.get('api_key')
    
    if not api_key or len(api_key) < 10:
        return jsonify({'success': False, 'error': 'Invalid API key'}), 400
    
    # Store in session (encrypted in production)
    session['ai_provider'] = provider
    session['api_key'] = api_key
    
    return jsonify({'success': True})

@bp.route('/api/ask', methods=['POST'])
def ask():
    dataset_id = session.get('dataset_id')
    msg = request.json.get('message', '').lower()
    
    if not dataset_id:
        return jsonify({'reply': '❌ Please load a dataset first.'})
    
    df, name = current_app.dataset_store.load(dataset_id)
    
    # Predefined query handlers
    if 'how many rows' in msg or 'how many columns' in msg or 'rows and columns' in msg:
        reply = f"📊 **Dataset Overview:**\n\n"
        reply += f"• **Rows:** {len(df):,}\n"
        reply += f"• **Columns:** {len(df.columns)}\n"
        reply += f"• **Total cells:** {len(df) * len(df.columns):,}\n"
        reply += f"• **Memory usage:** {df.memory_usage(deep=True).sum() / 1024:.2f} KB"
        
    elif 'missing' in msg or 'null' in msg:
        missing_count = int(df.isnull().sum().sum())
        missing_pct = (missing_count / (len(df) * len(df.columns))) * 100
        
        reply = f"⚠️ **Missing Values Analysis:**\n\n"
        reply += f"• **Total missing:** {missing_count:,}\n"
        reply += f"• **Percentage:** {missing_pct:.2f}%\n\n"
        
        # Top 5 columns with most missing
        missing_by_col = df.isnull().sum()
        missing_by_col = missing_by_col[missing_by_col > 0].sort_values(ascending=False).head(5)
        
        if len(missing_by_col) > 0:
            reply += "**Top columns with missing values:**\n"
            for col, count in missing_by_col.items():
                pct = (count / len(df)) * 100
                reply += f"  - `{col}`: {count:,} ({pct:.1f}%)\n"
        else:
            reply += "✅ No missing values found! Your data is clean."
            
    elif 'dtype' in msg or 'type' in msg or 'column types' in msg:
        reply = f"🔍 **Column Data Types:**\n\n"
        
        type_counts = df.dtypes.value_counts()
        for dtype, count in type_counts.items():
            reply += f"• **{dtype}:** {count} columns\n"
        
        reply += "\n**Detailed breakdown:**\n"
        for col, dtype in df.dtypes.items():
            reply += f"  - `{col}`: {dtype}\n"
            
    elif 'summary' in msg or 'statistical' in msg or 'describe' in msg:
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) == 0:
            reply = "📋 No numeric columns found for statistical summary."
        else:
            desc = df[numeric_cols].describe()
            reply = f"📋 **Statistical Summary** ({len(numeric_cols)} numeric columns):\n\n"
            
            for col in numeric_cols[:5]:  # Show first 5
                reply += f"**{col}:**\n"
                reply += f"  • Mean: {desc[col]['mean']:.2f}\n"
                reply += f"  • Std: {desc[col]['std']:.2f}\n"
                reply += f"  • Min: {desc[col]['min']:.2f}\n"
                reply += f"  • Max: {desc[col]['max']:.2f}\n\n"
                
            if len(numeric_cols) > 5:
                reply += f"... and {len(numeric_cols) - 5} more columns"
                
    elif 'correlation' in msg or 'correlate' in msg:
        numeric_df = df.select_dtypes(include=[np.number])
        
        if numeric_df.shape[1] < 2:
            reply = "🔗 Need at least 2 numeric columns for correlation analysis."
        else:
            corr_matrix = numeric_df.corr()
            
            # Find top correlations (excluding diagonal)
            corr_pairs = []
            for i in range(len(corr_matrix.columns)):
                for j in range(i+1, len(corr_matrix.columns)):
                    col1 = corr_matrix.columns[i]
                    col2 = corr_matrix.columns[j]
                    corr_val = corr_matrix.iloc[i, j]
                    corr_pairs.append((col1, col2, abs(corr_val), corr_val))
            
            corr_pairs.sort(key=lambda x: x[2], reverse=True)
            
            reply = f"🔗 **Top Correlations:**\n\n"
            for col1, col2, abs_corr, corr in corr_pairs[:5]:
                direction = "positive" if corr > 0 else "negative"
                strength = "strong" if abs_corr > 0.7 else ("moderate" if abs_corr > 0.4 else "weak")
                reply += f"• `{col1}` ↔ `{col2}`: {corr:.3f} ({strength} {direction})\n"
                
    elif 'outlier' in msg or 'anomal' in msg:
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) == 0:
            reply = "🎯 No numeric columns found for outlier detection."
        else:
            reply = f"🎯 **Outlier Detection (IQR Method):**\n\n"
            
            total_outliers = 0
            for col in numeric_cols[:5]:  # First 5 columns
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower = Q1 - 1.5 * IQR
                upper = Q3 + 1.5 * IQR
                
                outliers = ((df[col] < lower) | (df[col] > upper)).sum()
                total_outliers += outliers
                pct = (outliers / len(df)) * 100
                
                reply += f"• `{col}`: {outliers:,} outliers ({pct:.1f}%)\n"
            
            reply += f"\n**Total outliers detected:** {total_outliers:,}"
            
    else:
        # Generic response or try to use AI if API key configured
        api_key = session.get('api_key')
        provider = session.get('ai_provider', 'openai')
        
        if api_key:
            # Try to use actual AI API
            try:
                if provider == 'openai':
                    import openai
                    client = openai.OpenAI(api_key=api_key)
                    
                    context = f"Dataset '{name}' has {len(df)} rows and {len(df.columns)} columns.\n"
                    context += f"Columns: {', '.join(df.columns.tolist()[:10])}"
                    
                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": f"You are a data analyst assistant. Context: {context}"},
                            {"role": "user", "content": msg}
                        ],
                        max_tokens=200
                    )
                    reply = response.choices[0].message.content
                    
                elif provider == 'anthropic':
                    import anthropic
                    client = anthropic.Anthropic(api_key=api_key)
                    
                    context = f"Dataset has {len(df)} rows, {len(df.columns)} columns"
                    
                    response = client.messages.create(
                        model="claude-haiku-4-5-20251001",
                        max_tokens=200,
                        system=f"Data analyst assistant. Context: {context}",
                        messages=[{"role": "user", "content": msg}]
                    )
                    reply = response.content[0].text
                    
                elif provider == 'gemini':
                    import google.generativeai as genai
                    genai.configure(api_key=api_key)
                    
                    model = genai.GenerativeModel('gemini-2.0-flash')
                    context = f"Dataset: {len(df)} rows, {len(df.columns)} columns"
                    
                    response = model.generate_content(f"{context}\n\nQuestion: {msg}")
                    reply = response.text
                    
            except Exception as e:
                reply = f"🤖 AI Response failed: {str(e)}\n\nPlease check your API key and try again."
        else:
            reply = f"💬 I received your question: \"{msg}\"\n\n"
            reply += "To get AI-powered responses:\n"
            reply += "1. Select an AI provider above\n"
            reply += "2. Enter your API key\n"
            reply += "3. Click Save\n\n"
            reply += "**Quick queries you can try:**\n"
            reply += "• How many rows and columns?\n"
            reply += "• Show missing values\n"
            reply += "• Column data types\n"
            reply += "• Statistical summary\n"
            reply += "• Top correlations\n"
            reply += "• Detect outliers"
    
    # Save to chat history
    history = session.get('chat_history', [])
    history.append({'role': 'user', 'content': msg})
    history.append({'role': 'assistant', 'content': reply})
    session['chat_history'] = history[-20:]  # Keep last 20 messages
    
    return jsonify({'reply': reply, 'history': history})
