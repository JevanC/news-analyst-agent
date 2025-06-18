from flask import Flask, request, render_template
from agent import create_agent, run_agent

app = Flask(__name__)
agent_executor = create_agent()

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        question = request.form.get('question')
        try:
            print("User Question:", question)
            response = run_agent(agent_executor=agent_executor, message=question)

            print("Agent Response:", response)
            ai_messages = [msg for msg in response.get('messages', []) if 'AIMessage' in str(type(msg))]
            final_output = ai_messages[-1].content if ai_messages else "No AI response found."
            return render_template('home.html', question=question, response=final_output)
        except Exception as e:
            return e
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')


if __name__ == '__main__':
    app.run(debug=True)